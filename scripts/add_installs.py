#!/usr/bin/env python3
"""
Manually record install/uninstall data from the Chrome Web Store Developer Dashboard.

Run:
    python scripts/add_installs.py

You can also pass arguments directly:
    python scripts/add_installs.py --date 2026-04-07 --total 312 --weekly-installs 45 --weekly-uninstalls 3
"""

import argparse
import json
import os
from datetime import date

DATA_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "installs.json"
)


def load():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f:
            return json.load(f)
    return {"entries": []}


def save(data):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def upsert(data, entry):
    entries = data["entries"]
    idx = next((i for i, e in enumerate(entries) if e["date"] == entry["date"]), None)
    if idx is not None:
        entries[idx] = entry
        print(f"Updated entry for {entry['date']}")
    else:
        entries.append(entry)
        print(f"Added entry for {entry['date']}")
    data["entries"] = sorted(entries, key=lambda e: e["date"])


def interactive():
    today = date.today().isoformat()
    print("=" * 50)
    print("  Add Install Data — WebYes Accessibility Checker")
    print("=" * 50)
    print("Open your Chrome Web Store Developer Dashboard:")
    print("  https://chrome.google.com/webstore/developer/dashboard")
    print()

    entry_date = input(f"Date [{today}]: ").strip() or today
    try:
        total   = int(input("Total installs (cumulative): ").strip())
        weekly_in  = int(input("Weekly installs (new installs this week): ").strip())
        weekly_out = int(input("Weekly uninstalls: ").strip())
    except ValueError:
        print("Error: please enter whole numbers only.")
        return

    return {
        "date": entry_date,
        "total_installs": total,
        "weekly_installs": weekly_in,
        "weekly_uninstalls": weekly_out,
    }


def main():
    parser = argparse.ArgumentParser(description="Record Chrome Web Store install data.")
    parser.add_argument("--date",              default=None)
    parser.add_argument("--total",             type=int, default=None)
    parser.add_argument("--weekly-installs",   type=int, default=None)
    parser.add_argument("--weekly-uninstalls", type=int, default=None)
    args = parser.parse_args()

    if all(v is not None for v in [args.total, args.weekly_installs, args.weekly_uninstalls]):
        entry = {
            "date": args.date or date.today().isoformat(),
            "total_installs": args.total,
            "weekly_installs": args.weekly_installs,
            "weekly_uninstalls": args.weekly_uninstalls,
        }
    else:
        entry = interactive()
        if entry is None:
            return

    data = load()
    upsert(data, entry)
    save(data)

    net = entry["weekly_installs"] - entry["weekly_uninstalls"]
    print(f"\nSummary for {entry['date']}:")
    print(f"  Total installs   : {entry['total_installs']:,}")
    print(f"  Weekly installs  : +{entry['weekly_installs']}")
    print(f"  Weekly uninstalls: -{entry['weekly_uninstalls']}")
    print(f"  Net weekly growth: {'+' if net >= 0 else ''}{net}")
    print(f"\nSaved to {DATA_FILE}")


if __name__ == "__main__":
    main()
