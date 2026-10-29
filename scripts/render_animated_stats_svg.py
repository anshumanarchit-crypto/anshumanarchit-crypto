#!/usr/bin/env python3
"""Generate an animated, theme-aware contribution stats card from data/contributions.json.

The SVG contains self-contained CSS/SMIL animation (no JavaScript or remote assets):
metric tiles enter in sequence, values count up, and monthly bars grow from the baseline.
Usage: python scripts/render_animated_stats_svg.py --theme dark --output stats.svg
       python scripts/render_animated_stats_svg.py --theme light --output stats-light.svg
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

THEMES = {
    "dark": {
        "bg": "#0A101F", "bg2": "#13243A", "tile": "#152A40", "frame": "#29435D",
        "muted": "#91A6BE", "ink": "#F3F7FC", "dim": "#7186A0", "cyan": "#22D3EE",
        "blue": "#3B82F6", "teal": "#2DD4BF", "green": "#34D399", "bar": "#14B8A6",
        "amber": "#F59E0B", "violet": "#A78BFA", "gradient_end": "#070C16",
    },
    "light": {
        "bg": "#F8FAFC", "bg2": "#EAF2F9", "tile": "#FFFFFF", "frame": "#CBD5E1",
        "muted": "#475569", "ink": "#0F172A", "dim": "#64748B", "cyan": "#0891B2",
        "blue": "#2563EB", "teal": "#0D9488", "green": "#059669", "bar": "#0F766E",
        "amber": "#B45309", "violet": "#7C3AED", "gradient_end": "#F1F5F9",
    },
}

W, H = 840, 880
PAD, TITLEBAR_H, GAP = 20, 32, 16
COLS, ROWS = 2, 3
TILE_W = (W - PAD * 2 - GAP) / 2
TILE_H = 150
TILES_TOP = TITLEBAR_H + PAD + 4
CHART_TOP = TILES_TOP + ROWS * TILE_H + (ROWS - 1) * GAP + GAP
TILE_STAGGER, SLIDE_DUR, COUNT_DUR, FRAMES = 0.15, 0.45, 1.2, 16
BAR_START, BAR_STAGGER, BAR_DUR = TILE_STAGGER * COLS * ROWS + 0.4, 0.06, 0.6


def fmt(value: int | float) -> str:
    if isinstance(value, float) and not value.is_integer():
        return f"{value:,.1f}"
    return f"{int(round(value)):,}"


def short_date(value: str) -> str:
    date = dt.date.fromisoformat(value)
    return f"{date.strftime('%b')} {date.day}"


def safe(value: object) -> str:
    return html.escape(str(value), quote=False)


def render(data: dict, theme_name: str) -> str:
    t = THEMES[theme_name]
    cur, longest, best = data["current_streak"], data["longest_streak"], data["best_day"]
    days_count = len(data["days"])
    monthly = data.get("monthly", [])[-12:]
    if not monthly:
        raise ValueError("data/contributions.json has no monthly contribution records")
    if days_count == 0:
        raise ValueError("data/contributions.json has no daily contribution records")

    cur_span = f"{short_date(cur['start'])} – {short_date(cur['end'])}" if cur.get("length") else "—"
    long_span = f"{short_date(longest['start'])} – {short_date(longest['end'])}" if longest.get("length") else "—"
    tiles = [
        ("current streak", cur["length"], " days", cur_span, t["teal"]),
        ("longest streak", longest["length"], " days", long_span, t["blue"]),
        ("contributions", data["total_contributions"], "", "in the last year", t["ink"]),
        ("active days", data["active_days"], f" / {days_count}", f"{data['active_days'] / days_count:.0%} of the year", t["teal"]),
        ("best day", best["count"], "", short_date(best["date"]), t["amber"]),
        ("avg / active day", data["avg_per_active_day"], "", "contributions", t["violet"]),
    ]

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Animated GitHub contribution statistics for anshumanarchit-crypto" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
        "<style>"
        f'.tile{{opacity:0;animation:enter {SLIDE_DUR}s ease-out both}}'
        '@keyframes enter{0%{opacity:0;transform:translateY(14px)}100%{opacity:1;transform:translateY(0)}}'
        f'.bar{{transform-box:fill-box;transform-origin:bottom;transform:scaleY(0);animation:grow {BAR_DUR}s cubic-bezier(.2,.8,.2,1) both}}'
        '@keyframes grow{to{transform:scaleY(1)}}'
        '@media (prefers-reduced-motion: reduce){.tile,.bar{opacity:1!important;transform:none!important;animation:none!important}}'
        "</style>",
        f'<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{t["bg2"]}"/><stop offset="1" stop-color="{t["gradient_end"]}"/></linearGradient></defs>',
        f'<rect width="{W}" height="{H}" rx="14" fill="url(#bg)"/>',
        f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="14" fill="none" stroke="{t["frame"]}"/>',
        f'<line x1="0" y1="{TITLEBAR_H}" x2="{W}" y2="{TITLEBAR_H}" stroke="{t["frame"]}"/>',
    ]
    for i, color in enumerate(("#FF6B6B", "#FBBF24", "#34D399")):
        parts.append(f'<circle cx="{PAD + i*16}" cy="{TITLEBAR_H/2}" r="5" fill="{color}"/>')
    parts.append(f'<text x="{W/2}" y="{TITLEBAR_H/2+4}" fill="{t["muted"]}" font-size="12" text-anchor="middle">anshumanarchit-crypto@github:~$ ./stats.sh</text>')

    for i, (label, value, suffix, caption, accent) in enumerate(tiles):
        col, row = i % COLS, i // COLS
        x, y = PAD + col * (TILE_W + GAP), TILES_TOP + row * (TILE_H + GAP)
        start = i * TILE_STAGGER
        count_start = start + SLIDE_DUR * 0.6
        parts.append(f'<g class="tile" style="animation-delay:{start:.2f}s">')
        parts.append(f'<rect x="{x:.1f}" y="{y}" width="{TILE_W:.1f}" height="{TILE_H}" rx="10" fill="{t["tile"]}" stroke="{t["frame"]}"/>')
        parts.append(f'<text x="{x+24:.1f}" y="{y+40}" fill="{t["muted"]}" font-size="20">$ {safe(label)}</text>')
        num_y = y + 100
        for k in range(1, FRAMES + 1):
            p = k / FRAMES
            current = value * (1 - (1-p)**3)
            turn_on = count_start + COUNT_DUR * (k - 1) / FRAMES
            turn_off = count_start + COUNT_DUR * k / FRAMES
            sets = f'<set attributeName="opacity" to="1" begin="{turn_on:.3f}s"/>'
            if k < FRAMES:
                sets += f'<set attributeName="opacity" to="0" begin="{turn_off:.3f}s"/>'
            parts.append(f'<text x="{x+24:.1f}" y="{num_y}" opacity="0" font-size="48" font-weight="700" fill="{accent}">{safe(fmt(current))}<tspan font-size="21" font-weight="400" fill="{t["muted"]}">{safe(suffix)}</tspan>{sets}</text>')
        parts.append(f'<text x="{x+24:.1f}" y="{y+132}" fill="{t["muted"]}" font-size="17">{safe(caption)}</text>')
        parts.append("</g>")

    chart_x, chart_w = PAD, W - PAD * 2
    chart_h = H - PAD - CHART_TOP
    parts.append(f'<g class="tile" style="animation-delay:{BAR_START-0.3:.2f}s"><rect x="{chart_x}" y="{CHART_TOP}" width="{chart_w}" height="{chart_h}" rx="10" fill="{t["tile"]}" stroke="{t["frame"]}"/><text x="{chart_x+24}" y="{CHART_TOP+40}" fill="{t["muted"]}" font-size="21">$ contributions / month</text></g>')
    plot_top, plot_bottom = CHART_TOP + 64, CHART_TOP + chart_h - 40
    plot_left, plot_right = chart_x + 24, chart_x + chart_w - 24
    slot = (plot_right - plot_left) / len(monthly)
    bar_w = slot * 0.62
    peak = max(int(item.get("total", 0)) for item in monthly) or 1
    for i, item in enumerate(monthly):
        value = max(0, int(item.get("total", 0)))
        height = max(2, (plot_bottom - plot_top) * value / peak)
        bx = plot_left + i * slot + (slot - bar_w) / 2
        fill = t["cyan"] if value == peak and value else t["bar"]
        delay = BAR_START + i * BAR_STAGGER
        parts.append(f'<rect class="bar" x="{bx:.1f}" y="{plot_bottom-height:.1f}" width="{bar_w:.1f}" height="{height:.1f}" rx="4" fill="{fill}" style="animation-delay:{delay:.2f}s"/>')
        month_label = dt.date.fromisoformat(item["month"] + "-01").strftime("%b")[0]
        parts.append(f'<text x="{bx+bar_w/2:.1f}" y="{plot_bottom+28}" fill="{t["muted"]}" font-size="17" text-anchor="middle">{safe(month_label)}</text>')
        if value == peak and value:
            parts.append(f'<text class="tile" style="animation-delay:{delay+BAR_DUR:.2f}s" x="{bx+bar_w/2:.1f}" y="{plot_bottom-height-10:.1f}" fill="{t["ink"]}" font-size="17" text-anchor="middle">{value:,}</text>')
    parts.append("</svg>")
    return "".join(parts)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--theme", choices=sorted(THEMES), required=True)
    parser.add_argument("--input", type=Path, default=ROOT / "data" / "contributions.json")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.input.is_file():
        parser.error(f"contribution data not found: {args.input}")
    data = json.loads(args.input.read_text(encoding="utf-8"))
    for field in ("days", "total_contributions", "active_days", "current_streak", "longest_streak", "best_day", "avg_per_active_day", "monthly"):
        if field not in data:
            parser.error(f"{args.input} is missing required field: {field}")
    svg = render(data, args.theme)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(svg, encoding="utf-8", newline="\n")
    print(f"Wrote {args.output} ({W} x {H}; theme={args.theme}; count-up and growing bars enabled)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
