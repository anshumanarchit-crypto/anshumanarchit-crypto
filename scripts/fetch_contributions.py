#!/usr/bin/env python3
"""Fetch the public GitHub contribution calendar for the configured profile owner."""
from __future__ import annotations
import datetime as dt
import json
import os
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup

USERNAME = os.environ.get("GH_PROFILE_USER", "anshumanarchit-crypto").strip()
OUT = Path(__file__).resolve().parents[1] / "data" / "contributions.json"
URL = f"https://github.com/users/{USERNAME}/contributions"


def fetch_days() -> list[dict]:
    response = requests.get(URL, headers={"User-Agent": "anshumanarchit-crypto-profile/1.0"}, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    cells = soup.select("td.ContributionCalendar-day")
    if not cells:
        # GitHub has changed this markup before; fail clearly instead of silently writing false zeros.
        raise RuntimeError("No contribution calendar cells found. GitHub may have changed its public calendar markup.")
    days = []
    for cell in cells:
        date = cell.get("data-date")
        if not date:
            continue
        tooltip_id = cell.get("id")
        tooltip = soup.find("tool-tip", attrs={"for": tooltip_id}) if tooltip_id else None
        label = (tooltip.get_text(" ", strip=True) if tooltip else "")
        if re.search(r"no contributions", label, re.I):
            count = 0
        else:
            match = re.search(r"(\d[\d,]*)\s+contributions?", label, re.I)
            if match:
                count = int(match.group(1).replace(",", ""))
            elif label:
                count = 0
            else:
                # Some calendar markup includes the contribution count in aria-label.
                label = " ".join(str(cell.get(k, "")) for k in ("aria-label", "data-level"))
                match = re.search(r"(\d[\d,]*)\s+contributions?", label, re.I)
                count = int(match.group(1).replace(",", "")) if match else 0
        days.append({"date": date, "count": count, "level": int(cell.get("data-level") or 0)})
    days.sort(key=lambda item: item["date"])
    if not days:
        raise RuntimeError("GitHub returned no dated contribution cells.")
    return days


def build_snapshot(days: list[dict]) -> dict:
    total = sum(item["count"] for item in days)
    active = sum(item["count"] > 0 for item in days)
    best = max(days, key=lambda item: item["count"])

    # Treat the last completed contribution day as the streak endpoint when today is empty,
    # matching the semantics used by common GitHub streak summaries.
    idx = len(days) - 1
    if idx >= 0 and days[idx]["count"] == 0:
        idx -= 1
    current_len = 0
    while idx >= 0 and days[idx]["count"] > 0:
        current_len += 1
        idx -= 1
    current = {
        "length": current_len,
        "start": days[idx + 1]["date"] if current_len else None,
        "end": days[len(days) - 1 if days[-1]["count"] > 0 else len(days) - 2]["date"] if current_len else None,
    }

    longest_len = run = 0
    longest_start = longest_end = None
    run_start = 0
    for i, item in enumerate(days):
        if item["count"] > 0:
            if run == 0:
                run_start = i
            run += 1
            if run > longest_len:
                longest_len = run
                longest_start, longest_end = days[run_start]["date"], item["date"]
        else:
            run = 0
    monthly_totals: dict[str, int] = {}
    for item in days:
        month = item["date"][:7]
        monthly_totals[month] = monthly_totals.get(month, 0) + item["count"]
    return {
        "username": USERNAME,
        "generated_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "range": {"start": days[0]["date"], "end": days[-1]["date"]},
        "total_contributions": total,
        "active_days": active,
        "avg_per_active_day": round(total / active, 1) if active else 0,
        "current_streak": current,
        "longest_streak": {"length": longest_len, "start": longest_start, "end": longest_end},
        "best_day": {"date": best["date"], "count": best["count"]},
        "monthly": [{"month": month, "total": count} for month, count in sorted(monthly_totals.items())],
        "days": days,
    }


if __name__ == "__main__":
    snapshot = build_snapshot(fetch_days())
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Updated {OUT}: {snapshot['total_contributions']} contributions / {snapshot['active_days']} active days")
