#!/usr/bin/env python3
"""
Scrape Chrome Web Store keyword rankings for the WebYes Accessibility Checker
and its competitors. Saves results to data/rankings/YYYY-MM-DD.json and
updates data/rankings/index.json.

Run:
    python scripts/scrape_rankings.py

Requirements:
    pip install playwright
    playwright install chromium
"""

import asyncio
import json
import os
import re
import sys
from datetime import date

from playwright.async_api import async_playwright

# ── Extension registry ──────────────────────────────────────────────────────

EXTENSIONS = {
    "webyes":                "nidjdackonjofdcclfbdcapbkgghcdjf",
    "silktide":              "mpobacholfblmnpnfbiomjkecoojakah",
    "siteimprove":           "djcglbmbegflehmbfleechkjhmedcopn",
    "accessible_web_helper": "gdnpkbipbholkoaggmlblpbmgemddbgb",
    "browserstack":          "fmkhjeeeojocenbconhndpiohohajokn",
    "axe_devtools":          "lhdoppojpmngadmnindnejefpokejbdd",
    "wave":                  "jbbplnpkjmmeebjpijfedlgcdilocofh",
}

# ── Keywords to track ───────────────────────────────────────────────────────

KEYWORDS = [
    "accessibility checker",
    "web accessibility checker",
    "WCAG checker",
    "accessibility audit",
    "ADA compliance checker",
    "color contrast checker",
    "accessibility testing",
    "screen reader test",
    "accessibility validator",
    "ARIA checker",
    "web accessibility tool",
    "WCAG compliance checker",
    "accessibility analyzer",
    "accessibility extension",
    "disability checker",
]

# ── Scraper ─────────────────────────────────────────────────────────────────

MAX_RESULTS = 50   # Track up to position 50
SCROLL_PAUSE = 2   # seconds between scrolls
REQUEST_PAUSE = 4  # seconds between keyword searches


async def scrape_keyword(page, keyword: str) -> dict:
    """
    Visit Chrome Web Store search for `keyword`.
    Returns {ext_key: rank_int_or_None} for each tracked extension.
    Rank is 1-based; None means not found in top MAX_RESULTS.
    """
    url = f"https://chromewebstore.google.com/search/{keyword.replace(' ', '%20')}?hl=en"

    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
        await asyncio.sleep(SCROLL_PAUSE)
    except Exception as exc:
        print(f"    [warn] page.goto failed: {exc}")
        return {k: None for k in EXTENSIONS}

    positions = {}          # ext_key -> rank
    seen_ids  = set()       # CWS extension IDs already counted
    position  = 1
    prev_count = 0

    while position <= MAX_RESULTS:
        links = await page.query_selector_all('a[href*="/detail/"]')

        for link in links:
            href = await link.get_attribute("href")
            if not href:
                continue
            # Extract extension ID: last path segment, strip query string
            ext_id = href.rstrip("/").split("/")[-1].split("?")[0]
            if not ext_id or len(ext_id) < 20 or ext_id in seen_ids:
                continue

            seen_ids.add(ext_id)

            for key, tracked_id in EXTENSIONS.items():
                if ext_id == tracked_id and key not in positions:
                    positions[key] = position

            position += 1

        # Stop if all found or we have enough
        if len(positions) == len(EXTENSIONS) or position > MAX_RESULTS:
            break

        # Scroll to load more results
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(SCROLL_PAUSE)

        new_links = await page.query_selector_all('a[href*="/detail/"]')
        if len(new_links) == prev_count:
            break  # No new results loaded — end of list
        prev_count = len(new_links)

    # Extensions not found → None
    for key in EXTENSIONS:
        if key not in positions:
            positions[key] = None

    return positions


async def scrape_user_count(page):
    """
    Visit the WebYes extension page and extract the public user count.
    Returns an integer or None if not found.
    """
    url = f"https://chromewebstore.google.com/detail/accessibility-checker-by/{EXTENSIONS['webyes']}"
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
        await asyncio.sleep(2)
        content = await page.content()
        # CWS shows counts like "1,234 users" or "10,000+ users"
        match = re.search(r'([\d,]+)\+?\s*users', content, re.IGNORECASE)
        if match:
            return int(match.group(1).replace(",", ""))
    except Exception as exc:
        print(f"  [warn] Could not scrape user count: {exc}")
    return None


async def main():
    today      = date.today().isoformat()
    repo_root  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = os.path.join(repo_root, "data", "rankings")
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"{today}.json")

    results = {"date": today, "keywords": {}}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            locale="en-US",
        )
        page = await context.new_page()

        # Scrape user count from extension page
        print("Fetching user count from extension page ...", end=" ", flush=True)
        user_count = await scrape_user_count(page)
        if user_count is not None:
            print(f"{user_count:,} users")
            results["user_count"] = user_count
            # Auto-update installs.json
            installs_file = os.path.join(repo_root, "data", "installs.json")
            if os.path.exists(installs_file):
                with open(installs_file) as f:
                    installs_data = json.load(f)
            else:
                installs_data = {"entries": []}
            entries = installs_data.get("entries", [])
            existing = next((e for e in entries if e["date"] == today), None)
            if existing:
                existing["total_installs"] = user_count
            else:
                entries.append({"date": today, "total_installs": user_count, "weekly_installs": None, "weekly_uninstalls": None})
            installs_data["entries"] = sorted(entries, key=lambda e: e["date"])
            os.makedirs(os.path.dirname(installs_file), exist_ok=True)
            with open(installs_file, "w") as f:
                json.dump(installs_data, f, indent=2)
            print(f"  Auto-saved user count to data/installs.json")
        else:
            print("not found — check extension page manually")

        await asyncio.sleep(REQUEST_PAUSE)

        for i, keyword in enumerate(KEYWORDS, 1):
            print(f"[{i}/{len(KEYWORDS)}] Scraping: '{keyword}' ...", end=" ", flush=True)
            try:
                positions = await scrape_keyword(page, keyword)
                results["keywords"][keyword] = positions
                webyes_rank = positions.get("webyes")
                print(f"WebYes → {'#' + str(webyes_rank) if webyes_rank else 'not found'}")
            except Exception as exc:
                print(f"ERROR: {exc}")
                results["keywords"][keyword] = {k: None for k in EXTENSIONS}

            if i < len(KEYWORDS):
                await asyncio.sleep(REQUEST_PAUSE)

        await browser.close()

    # Save daily file
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved: {output_file}")

    # Update index.json
    index_file = os.path.join(output_dir, "index.json")
    if os.path.exists(index_file):
        with open(index_file) as f:
            index = json.load(f)
    else:
        index = []

    if today not in index:
        index.append(today)
        index.sort()

    with open(index_file, "w") as f:
        json.dump(index, f, indent=2)
    print(f"Updated: {index_file}")


if __name__ == "__main__":
    asyncio.run(main())
