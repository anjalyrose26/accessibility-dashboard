#!/usr/bin/env python3
"""
Post a daily summary to Slack after the scraper runs.
Reads today's and yesterday's ranking data and formats a clean message.

Usage:
    SLACK_WEBHOOK_URL=https://hooks.slack.com/... python scripts/notify_slack.py
"""

import json
import os
import sys
import urllib.request
import urllib.error
from datetime import date, timedelta

REPO_ROOT  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR   = os.path.join(REPO_ROOT, "data")
RANK_DIR   = os.path.join(DATA_DIR, "rankings")
DASHBOARD  = "https://anjalyrose26.github.io/accessibility-dashboard/"

WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")
if not WEBHOOK_URL:
    print("Error: SLACK_WEBHOOK_URL environment variable not set.")
    sys.exit(1)


def load_json(path):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return None


def rank_str(rank):
    if rank is None:
        return "—"
    return f"#{rank}"


def change_str(current, previous):
    if current is None and previous is None:
        return ""
    if previous is None:
        return " _(new)_"
    if current is None:
        return " _(dropped out)_"
    diff = previous - current  # positive = improved
    if diff == 0:
        return " _(no change)_"
    arrow = "↑" if diff > 0 else "↓"
    return f" *{arrow}{abs(diff)}*"


def main():
    today     = date.today().isoformat()
    yesterday = (date.today() - timedelta(days=1)).isoformat()

    today_data     = load_json(os.path.join(RANK_DIR, f"{today}.json"))
    yesterday_data = load_json(os.path.join(RANK_DIR, f"{yesterday}.json"))
    installs_data  = load_json(os.path.join(DATA_DIR, "installs.json"))

    if not today_data:
        print("No ranking data for today — skipping Slack notification.")
        sys.exit(0)

    # User count
    entries      = (installs_data or {}).get("entries", [])
    today_entry  = next((e for e in entries if e["date"] == today), None)
    user_count   = today_entry["total_installs"] if today_entry else None

    prev_entry   = next((e for e in entries if e["date"] == yesterday), None)
    prev_count   = prev_entry["total_installs"] if prev_entry else None

    user_line = f"*👥 Users:* {user_count:,}" if user_count else "*👥 Users:* —"
    if user_count and prev_count:
        diff = user_count - prev_count
        if diff != 0:
            user_line += f"  ({'+' if diff > 0 else ''}{diff} vs yesterday)"

    # Rankings for WebYes
    keywords = today_data.get("keywords", {})
    ranked   = [(kw, data["webyes"]) for kw, data in keywords.items() if data.get("webyes") is not None]
    unranked = [(kw, None)           for kw, data in keywords.items() if data.get("webyes") is None]

    ranked.sort(key=lambda x: x[1])

    rank_lines = []
    for kw, rank in ranked:
        prev_rank = (yesterday_data or {}).get("keywords", {}).get(kw, {}).get("webyes") if yesterday_data else None
        rank_lines.append(f"  • `{kw}` → *#{rank}*{change_str(rank, prev_rank)}")

    if unranked:
        rank_lines.append(f"  • _{len(unranked)} keywords: not in top 50_")

    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": f"📊 Daily CWS Report — {today}"}
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": user_line}
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*🔑 WebYes Keyword Rankings:*\n" + "\n".join(rank_lines)
            }
        },
        {
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": f"<{DASHBOARD}|Open Dashboard>"}]
        }
    ]

    payload = json.dumps({"blocks": blocks}).encode("utf-8")
    req = urllib.request.Request(WEBHOOK_URL, data=payload, headers={"Content-Type": "application/json"})

    try:
        urllib.request.urlopen(req, timeout=10)
        print("Slack notification sent.")
    except urllib.error.URLError as e:
        print(f"Failed to send Slack notification: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
