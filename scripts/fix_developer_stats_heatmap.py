#!/usr/bin/env python3
"""Repair only the broken developer-stats cards and annual contribution heatmap.

Reads data/contributions.json, writes twelve self-hosted animated GIFs, rewires only
matching image blocks in README.md, and adds this generator to the existing
Update profile art workflow (when a recognizable commit step is present).
It deliberately does not edit other README sections or contribution source data.
"""
from __future__ import annotations

import datetime as dt
import html
import json
import math
import os
import re
import sys
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "contributions.json"
README_PATH = ROOT / "README.md"
ASSET_DIR = ROOT / "assets" / "animated"

THEMES = {
    "dark": {
        "bg": "#0B1018", "panel": "#0F1A2B", "panel2": "#14243A", "border": "#2A4564",
        "text": "#F2F7FF", "muted": "#9DB2CB", "dim": "#7187A3", "blue": "#4D8DFF",
        "cyan": "#32D8EA", "teal": "#36D6BE", "amber": "#FFB547", "violet": "#B59BFF",
        "empty": "#1A2637", "levels": ["#1A2637", "#134B42", "#127668", "#169D8C", "#35CDB8"],
        "scan": "#38E4D0", "grid": "#203247"
    },
    "light": {
        "bg": "#F5F8FC", "panel": "#FFFFFF", "panel2": "#EAF1F9", "border": "#C9D8E9",
        "text": "#152A43", "muted": "#526A84", "dim": "#70859D", "blue": "#2563EB",
        "cyan": "#0891B2", "teal": "#0F9F92", "amber": "#B96A0A", "violet": "#7C3AED",
        "empty": "#E2E9F2", "levels": ["#E2E9F2", "#C4EDE5", "#8CDCCD", "#43BEA9", "#087F70"],
        "scan": "#0EA5A4", "grid": "#D6E1ED"
    }
}

FONT_CANDIDATES = {
    "sans": [r"C:\Windows\Fonts\arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"],
    "sansb": [r"C:\Windows\Fonts\arialbd.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"],
    "mono": [r"C:\Windows\Fonts\consola.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"],
    "monob": [r"C:\Windows\Fonts\consolab.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"],
}


def font(size: int, kind: str = "sans") -> ImageFont.ImageFont:
    for candidate in FONT_CANDIDATES[kind]:
        try:
            if Path(candidate).exists():
                return ImageFont.truetype(candidate, size=size)
        except OSError:
            pass
    return ImageFont.load_default()


def rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def rounded(draw: ImageDraw.ImageDraw, xy, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def fresh_background(size: tuple[int, int], theme: dict[str, Any]) -> Image.Image:
    im = Image.new("RGB", size, theme["bg"])
    d = ImageDraw.Draw(im)
    w, h = size
    start, end = rgb(theme["bg"]), rgb(theme["panel"])
    for x in range(w):
        t = x / max(1, w - 1)
        c = tuple(round(start[i] * (1 - t * 0.18) + end[i] * (t * 0.18)) for i in range(3))
        d.line((x, 0, x, h), fill=c)
    return im


def save_loop(frames: list[Image.Image], path: Path, duration: int = 90) -> None:
    if not frames:
        raise ValueError(f"No frames for {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    palette = frames[len(frames) // 2].convert("RGB").quantize(colors=128, method=Image.Quantize.MEDIANCUT)
    converted = [frame.convert("RGB").quantize(palette=palette, dither=Image.Dither.NONE) for frame in frames]
    converted[0].save(path, save_all=True, append_images=converted[1:], duration=duration,
                       loop=0, optimize=True, disposal=2)


def parse_snapshot(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing {path}. Run scripts/fetch_contributions.py first.")
    data = json.loads(path.read_text(encoding="utf-8"))
    required = {"days", "total_contributions", "active_days", "current_streak", "longest_streak", "best_day", "monthly"}
    missing = sorted(required - set(data))
    if missing:
        raise ValueError(f"data/contributions.json is missing fields: {', '.join(missing)}")
    if not data["days"]:
        raise ValueError("data/contributions.json contains no daily contribution records")
    for item in data["days"]:
        dt.date.fromisoformat(item["date"])
        if not isinstance(item.get("count"), (int, float)):
            raise ValueError(f"Invalid contribution count for {item.get('date')}")
    return data



def draw_overview_card(theme: dict[str, Any], data: dict[str, Any], frame_index: int, total_frames: int = 42) -> Image.Image:
    """Wide contribution overview; values match the annual heatmap snapshot."""
    W, H = 1120, 285
    im = fresh_background((W, H), theme)
    d = ImageDraw.Draw(im)
    rounded(d, (2, 2, W - 3, H - 3), 18, theme["panel"], theme["border"], 2)
    d.rounded_rectangle((3, 3, W - 4, 42), radius=16, fill=theme["panel2"])
    d.rectangle((3, 26, W - 4, 42), fill=theme["panel2"])
    for i, col in enumerate(("#FF6B6B", "#FBBF24", "#34D399")):
        d.ellipse((18 + i * 13, 16, 25 + i * 13, 23), fill=col)
    d.text((W / 2, 13), "ARCHIT ANSHUMAN  /  GITHUB DEVELOPER STATS", font=font(11, "monob"), fill=theme["muted"], anchor="mt")
    metrics = [
        ("TOTAL CONTRIBUTIONS", f"{int(data['total_contributions']):,}", theme["blue"], "last 12 months"),
        ("ACTIVE DAYS", f"{int(data['active_days']):,}", theme["teal"], "days with activity"),
        ("CURRENT STREAK", f"{int(data['current_streak']['length'])} " + ("day" if int(data['current_streak']['length']) == 1 else "days"), theme["amber"], "consecutive days"),
    ]
    x0, gap = 18, 16
    card_w = (W - 36 - gap * 2) // 3
    for i, (label, value, accent, caption) in enumerate(metrics):
        x = x0 + i * (card_w + gap)
        rounded(d, (x, 56, x + card_w, 174), 12, theme["panel2"], theme["border"], 1)
        d.text((x + 18, 71), label, font=font(11, "monob"), fill=theme["muted"])
        d.text((x + 18, 96), value, font=font(31, "sansb"), fill=accent)
        d.text((x + 18, 145), caption, font=font(10, "mono"), fill=theme["dim"])
        if i == 1:
            cx = x + card_w - 50
            cy = 110
            r = 26
            d.ellipse((cx-r, cy-r, cx+r, cy+r), outline=theme["border"], width=5)
            extent = int(360 * ((frame_index % total_frames) / max(1, total_frames - 1)))
            d.arc((cx-r, cy-r, cx+r, cy+r), -90, -90 + extent, fill=theme["cyan"], width=5)
    d.line((18, 200, W - 18, 200), fill=theme["border"], width=1)
    d.text((20, 216), f"LONGEST STREAK  {int(data['longest_streak']['length'])} DAYS", font=font(11, "monob"), fill=theme["muted"])
    d.text((W - 20, 216), f"BEST DAY  {int(data['best_day']['count'])}  ·  {data['best_day']['date']}", font=font(11, "monob"), fill=theme["amber"], anchor="rt")
    scan_x = 18 + int((frame_index / max(1, total_frames - 1)) * (W - 36))
    d.line((18, 267, W - 18, 267), fill=theme["border"], width=1)
    d.line((max(18, scan_x - 70), 267, min(W - 18, scan_x + 34), 267), fill=theme["cyan"], width=3)
    d.ellipse((max(18, scan_x - 3), 264, min(W - 18, scan_x + 3), 270), fill=theme["teal"])
    return im


def draw_activity_graph(theme: dict[str, Any], data: dict[str, Any], frame_index: int, total_frames: int = 42) -> Image.Image:
    """Looping 31-day line chart rendered from the same data snapshot."""
    W, H = 1120, 320
    im = fresh_background((W, H), theme)
    d = ImageDraw.Draw(im)
    rounded(d, (2, 2, W - 3, H - 3), 18, theme["panel"], theme["border"], 2)
    d.rounded_rectangle((3, 3, W - 4, 40), radius=15, fill=theme["panel2"])
    d.rectangle((3, 25, W - 4, 40), fill=theme["panel2"])
    for i, col in enumerate(("#FF6B6B", "#FBBF24", "#34D399")):
        d.ellipse((18 + i * 13, 15, 25 + i * 13, 22), fill=col)
    d.text((W / 2, 12), "RECENT GITHUB ACTIVITY  /  LAST 31 DAYS", font=font(11, "monob"), fill=theme["muted"], anchor="mt")
    days = data["days"][-31:]
    vals = [int(item.get("count", 0)) for item in days]
    max_val = max(vals + [1])
    left, right, top, bottom = 68, W - 36, 72, 250
    y_labels = {0: max_val, 4: 0}
    if max_val >= 3:
        y_labels[2] = max_val // 2
    for i in range(5):
        y = top + i * (bottom - top) / 4
        d.line((left, y, right, y), fill=theme["grid"], width=1)
        if i in y_labels:
            d.text((24, y - 5), str(y_labels[i]), font=font(9, "mono"), fill=theme["dim"])
    points = [(left + i * (right-left) / max(1, len(vals)-1), bottom - v / max_val * (bottom-top)) for i, v in enumerate(vals)]
    if points:
        d.line(points, fill=theme["border"], width=2)
        for x, y in points:
            d.ellipse((x-2, y-2, x+2, y+2), fill=theme["dim"])
        progress = int((frame_index / max(1, total_frames-1)) * (len(points)-1))
        if progress > 0:
            d.line(points[:progress+1], fill=theme["blue"], width=3)
        x, y = points[progress]
        d.ellipse((x-7, y-7, x+7, y+7), fill=theme["cyan"])
        d.ellipse((x-3, y-3, x+3, y+3), fill=theme["text"])
        first_label = dt.date.fromisoformat(days[0]["date"]).strftime("%b %d")
        last_label = dt.date.fromisoformat(days[-1]["date"]).strftime("%b %d")
        d.text((left, 271), first_label, font=font(9, "mono"), fill=theme["muted"])
        d.text((right, 271), last_label, font=font(9, "mono"), fill=theme["muted"], anchor="rt")
    d.text((W-28, 49), f"{sum(vals)} contributions", font=font(10, "monob"), fill=theme["teal"], anchor="rt")
    return im

def draw_stats_card(theme: dict[str, Any], data: dict[str, Any], frame_index: int, total_frames: int = 42) -> Image.Image:
    W, H = 550, 292
    im = fresh_background((W, H), theme)
    d = ImageDraw.Draw(im)
    rounded(d, (2, 2, W - 3, H - 3), 17, theme["panel"], theme["border"], 2)
    d.rounded_rectangle((3, 3, W - 4, 42), radius=15, fill=theme["panel2"])
    d.rectangle((3, 27, W - 4, 42), fill=theme["panel2"])
    for i, c in enumerate(("#FF6B6B", "#FBBF24", "#34D399")):
        d.ellipse((18 + i * 13, 16, 25 + i * 13, 23), fill=c)
    d.text((W / 2, 14), "ARCHIT ANSHUMAN  /  ACTIVITY SNAPSHOT", font=font(10, "monob"), fill=theme["muted"], anchor="mt")

    metrics = [
        ("CONTRIBUTIONS", f"{int(data['total_contributions']):,}", theme["blue"], "last year"),
        ("ACTIVE DAYS", f"{int(data['active_days']):,}", theme["teal"], "with activity"),
        ("CURRENT STREAK", f"{int(data['current_streak']['length'])}d", theme["amber"], "consecutive days"),
        ("LONGEST STREAK", f"{int(data['longest_streak']['length'])}d", theme["violet"], "consecutive days"),
    ]
    tile_w, tile_h = 244, 75
    positions = [(18, 55), (288, 55), (18, 139), (288, 139)]
    for (label, value, color, caption), (x, y) in zip(metrics, positions):
        rounded(d, (x, y, x + tile_w, y + tile_h), 10, theme["panel2"], theme["border"], 1)
        d.text((x + 12, y + 8), label, font=font(9, "monob"), fill=theme["muted"])
        d.text((x + 12, y + 27), value, font=font(24, "sansb"), fill=color)
        d.text((x + tile_w - 10, y + 49), caption, font=font(8, "mono"), fill=theme["dim"], anchor="rt")

    d.text((18, 227), "MONTHLY CONTRIBUTION PULSE", font=font(9, "monob"), fill=theme["muted"])
    monthly = data.get("monthly", [])[-12:]
    if not monthly:
        monthly = [{"month": "2026-01", "total": 0}]
    peak = max([int(m.get("total", 0)) for m in monthly] + [1])
    chart_x, chart_y, chart_w, chart_h = 18, 244, 514, 30
    slot = chart_w / len(monthly)
    sweep = (frame_index / max(1, total_frames - 1)) * (chart_w + 70) - 35
    d.line((chart_x, chart_y + chart_h, chart_x + chart_w, chart_y + chart_h), fill=theme["border"], width=1)
    for i, item in enumerate(monthly):
        val = int(item.get("total", 0))
        bar_h = max(2, int((chart_h - 4) * val / peak)) if val else 2
        x0 = chart_x + i * slot + slot * 0.25
        x1 = chart_x + (i + 1) * slot - slot * 0.25
        y0 = chart_y + chart_h - bar_h
        col = theme["cyan"] if x0 <= sweep <= x1 else theme["teal"]
        rounded(d, (int(x0), y0, int(x1), chart_y + chart_h), 3, col)
    # A subtle scanning accent loops without hiding any metrics.
    sx = int(5 + (frame_index / max(1, total_frames - 1)) * (W - 40))
    d.line((5, 285, W - 5, 285), fill=theme["border"], width=1)
    d.line((max(5, sx - 42), 285, min(W - 5, sx + 42), 285), fill=theme["cyan"], width=3)
    d.ellipse((max(5, sx - 3), 282, min(W - 5, sx + 3), 288), fill=theme["amber"])
    return im



def draw_contribution_detail_card(theme: dict[str, Any], data: dict[str, Any], frame_index: int, total_frames: int = 42) -> Image.Image:
    """Vertical stats card used beside the portrait; keeps the original two-column layout."""
    W, H = 840, 800
    im = fresh_background((W, H), theme)
    d = ImageDraw.Draw(im)
    rounded(d, (3, 3, W - 4, H - 4), 18, theme["panel"], theme["border"], 2)
    d.rounded_rectangle((4, 4, W - 5, 44), radius=15, fill=theme["panel2"])
    d.rectangle((4, 27, W - 5, 44), fill=theme["panel2"])
    for i, col in enumerate(("#FF6B6B", "#FBBF24", "#34D399")):
        d.ellipse((20 + i * 13, 16, 27 + i * 13, 23), fill=col)
    d.text((W / 2, 13), "anshumanarchit-crypto@github:~$ ./stats.sh", font=font(10, "mono"), fill=theme["muted"], anchor="mt")
    metrics = [
        ("current streak", f"{int(data['current_streak']['length'])}", "days", theme["teal"]),
        ("longest streak", f"{int(data['longest_streak']['length'])}", "days", theme["blue"]),
        ("contributions", f"{int(data['total_contributions']):,}", "in the last year", theme["text"]),
        ("active days", f"{int(data['active_days']):,}", f"/ {len(data['days'])} days", theme["teal"]),
        ("best day", f"{int(data['best_day']['count'])}", str(data['best_day']['date']), theme["amber"]),
        ("avg / active day", f"{float(data['avg_per_active_day']):.1f}", "contributions", theme["violet"]),
    ]
    for i, (label, value, suffix, accent) in enumerate(metrics):
        x = 20 + (i % 2) * 401
        y = 62 + (i // 2) * 111
        rounded(d, (x, y, x + 385, y + 96), 11, theme["panel2"], theme["border"], 1)
        d.text((x + 16, y + 12), "$ " + label, font=font(11, "mono"), fill=theme["muted"])
        d.text((x + 16, y + 36), value, font=font(27, "monob"), fill=accent)
        d.text((x + 16, y + 72), suffix, font=font(9, "mono"), fill=theme["dim"])
    chart_y = 408
    rounded(d, (20, chart_y, 820, 758), 13, theme["bg"], theme["border"], 1)
    d.text((40, chart_y + 18), "$ contributions / month", font=font(12, "mono"), fill=theme["muted"])
    monthly = data.get("monthly", [])[-12:]
    if not monthly:
        monthly = [{"month": "2026-01", "total": 0}]
    left, right, top, bottom = 44, 800, chart_y + 74, chart_y + 257
    peak = max([int(item.get("total", 0)) for item in monthly] + [1])
    slot = (right - left) / len(monthly)
    sweep = left + int((frame_index / max(1, total_frames - 1)) * (right - left))
    for i, item in enumerate(monthly):
        val = int(item.get("total", 0))
        bh = max(3, int((bottom - top) * val / peak)) if val else 3
        x0 = left + i * slot + slot * 0.20
        x1 = left + (i + 1) * slot - slot * 0.20
        y0 = bottom - bh
        col = theme["cyan"] if x0 <= sweep <= x1 else (theme["teal"] if val == peak and val else theme["teal"])
        rounded(d, (int(x0), y0, int(x1), bottom), 4, col)
        month_name = dt.date.fromisoformat(item["month"] + "-01").strftime("%b")
        d.text(((x0+x1)/2, bottom + 13), month_name, font=font(8, "mono"), fill=theme["dim"], anchor="mt")
        if val and val == peak:
            d.text(((x0+x1)/2, y0 - 16), str(val), font=font(9, "monob"), fill=theme["text"], anchor="mt")
    d.text((40, 713), f"ONE SNAPSHOT  ·  {int(data['total_contributions'])} CONTRIBUTIONS  ·  {int(data['active_days'])} ACTIVE DAYS", font=font(9, "mono"), fill=theme["teal"])
    scan = left + int((frame_index / max(1, total_frames-1)) * (right-left))
    d.line((24, 780, W-24, 780), fill=theme["border"], width=1)
    d.line((max(24, scan-52), 780, min(W-24, scan+28), 780), fill=theme["cyan"], width=3)
    return im


def contribution_stats_picture() -> str:
    return ('<picture><source media="(prefers-color-scheme: dark)" srcset="./assets/animated/contribution-stats-dark.gif" />'
            '<source media="(prefers-color-scheme: light)" srcset="./assets/animated/contribution-stats-light.gif" />'
            '<img src="./assets/animated/contribution-stats-dark.gif" width="100%" alt="Animated contribution totals, streaks, active days and monthly activity from the same JSON snapshot" /></picture>')

def draw_toolkit_card(theme: dict[str, Any], frame_index: int, total_frames: int = 42) -> Image.Image:
    W, H = 550, 292
    im = fresh_background((W, H), theme)
    d = ImageDraw.Draw(im)
    rounded(d, (2, 2, W - 3, H - 3), 17, theme["panel"], theme["border"], 2)
    d.rounded_rectangle((3, 3, W - 4, 42), radius=15, fill=theme["panel2"])
    d.rectangle((3, 27, W - 4, 42), fill=theme["panel2"])
    for i, c in enumerate(("#FF6B6B", "#FBBF24", "#34D399")):
        d.ellipse((18 + i * 13, 16, 25 + i * 13, 23), fill=c)
    d.text((W / 2, 14), "LANGUAGES & AI TOOLKIT", font=font(10, "monob"), fill=theme["muted"], anchor="mt")
    d.text((W - 15, 51), "FROM ARCHIT'S RESUME", font=font(7, "monob"), fill=theme["dim"], anchor="rt")

    groups = [
        ("LANGUAGES", ["Python", "C++", "JavaScript", "C", "MySQL"], theme["blue"]),
        ("AGENTIC AI", ["LangGraph", "CrewAI", "AutoGen", "n8n", "OpenAI Agents SDK"], theme["cyan"]),
        ("AI / DATA", ["NLP", "Computer Vision", "LSTM", "Transformers", "XGBoost"], theme["violet"]),
        ("BACKEND", ["FastAPI", "Node.js", "Express.js", "REST APIs", "MongoDB", "ChromaDB"], theme["amber"]),
    ]
    y = 65
    for gi, (label, chips, accent) in enumerate(groups):
        rounded(d, (14, y, W - 14, y + 48), 8, theme["panel2"], theme["border"], 1)
        d.rounded_rectangle((14, y, 18, y + 48), radius=2, fill=accent)
        d.text((27, y + 7), label, font=font(8, "monob"), fill=accent)
        # Chips flow in one row with safe truncation; no fabricated usage percentages.
        x = 115
        for chip in chips:
            label_f = font(8, "sansb")
            tw = int(d.textlength(chip, font=label_f)) + 13
            if x + tw > W - 23:
                break
            rounded(d, (x, y + 8, x + tw, y + 29), 6, theme["bg"], accent, 1)
            d.text((x + tw / 2, y + 12), chip, font=label_f, fill=theme["text"], anchor="mt")
            x += tw + 5
        y += 52
    d.text((15, 276), "PROGRAMMING  ·  ORCHESTRATION  ·  RETRIEVAL  ·  APPLICATION ENGINEERING", font=font(7, "mono"), fill=theme["muted"])
    scan = int(8 + (frame_index / max(1, total_frames - 1)) * (W - 16))
    d.line((8, 286, W - 8, 286), fill=theme["border"], width=1)
    d.line((max(8, scan - 36), 286, min(W - 8, scan + 36), 286), fill=theme["cyan"], width=3)
    return im


def build_weeks(data: dict[str, Any]):
    day_map = {dt.date.fromisoformat(item["date"]): item for item in data["days"]}
    dates = sorted(day_map)
    first, last = dates[0], dates[-1]
    # GitHub-style week columns begin on Sunday, with Sunday in the top row.
    start = first - dt.timedelta(days=(first.weekday() + 1) % 7)
    end = last + dt.timedelta(days=6 - ((last.weekday() + 1) % 7))
    count = ((end - start).days + 1) // 7
    weeks = []
    for col in range(count):
        week = []
        for row in range(7):
            day = start + dt.timedelta(days=col * 7 + row)
            week.append((day, day_map.get(day)))
        weeks.append(week)
    return weeks, start, end


def draw_heatmap(theme: dict[str, Any], data: dict[str, Any], frame_index: int, total_frames: int = 48) -> Image.Image:
    W, H = 1120, 270
    im = fresh_background((W, H), theme)
    d = ImageDraw.Draw(im)
    rounded(d, (2, 2, W - 3, H - 3), 17, theme["panel"], theme["border"], 1)
    d.rounded_rectangle((3, 3, W - 4, 39), radius=14, fill=theme["panel2"])
    d.rectangle((3, 25, W - 4, 39), fill=theme["panel2"])
    d.ellipse((16, 15, 24, 23), fill=theme["teal"])
    d.text((W / 2, 12), "ANNUAL CONTRIBUTION HEATMAP", font=font(12, "sansb"), fill=theme["text"], anchor="mt")
    username = str(data.get("username", "anshumanarchit-crypto"))
    d.text((W / 2, 44), f"{username} / contribution field", font=font(8, "mono"), fill=theme["muted"], anchor="mt")

    weeks, start, end = build_weeks(data)
    left, right = 50, 23
    available = W - left - right
    step_x = available / max(1, len(weeks))
    cell = min(14, max(10, int(step_x - 4)))
    top, step_y = 75, 18
    # Month labels are drawn at the first actual day-of-month in the data window.
    # This deliberately skips a partial previous month, preventing the "OctNov" overlap.
    labels = {}
    for ci, week in enumerate(weeks):
        for day, item in week:
            if day.day == 1 and item is not None:
                labels.setdefault((day.year, day.month), (ci, day.strftime("%b")))
    for _, (ci, label) in sorted(labels.items(), key=lambda kv: kv[1][0]):
        x = left + ci * step_x
        d.text((x, 60), label, font=font(10, "sans"), fill=theme["muted"])

    # Keep the seven-row field fully visible in every frame; animate only the scan accent.
    for row, label in [(1, "Mon"), (3, "Wed"), (5, "Fri")]:
        d.text((12, top + row * step_y + cell / 2), label, font=font(10, "sans"), fill=theme["muted"], anchor="lm")
    active_cells = []
    level_colours = theme["levels"]
    for ci, week in enumerate(weeks):
        x = int(left + ci * step_x)
        for ri, (day, item) in enumerate(week):
            if item is None:
                continue
            n = int(item.get("count", 0))
            level = 0 if n <= 0 else 1 if n <= 1 else 2 if n <= 3 else 3 if n <= 7 else 4
            y = top + ri * step_y
            rounded(d, (x, y, x + cell, y + cell), 3, level_colours[level])
            if n > 0:
                active_cells.append((x, y, n))

    # Moving light sweep under the grid provides a continuous loop without blanking data.
    progress = frame_index / max(1, total_frames - 1)
    sweep = left + int(progress * (available - 1))
    grid_bottom = top + 6 * step_y + cell
    d.line((left, grid_bottom + 9, W - right, grid_bottom + 9), fill=theme["border"], width=1)
    d.line((left, grid_bottom + 9, sweep, grid_bottom + 9), fill=theme["blue"], width=2)
    d.line((max(left, sweep - 45), grid_bottom + 9, min(W - right, sweep + 22), grid_bottom + 9), fill=theme["cyan"], width=3)
    if active_cells:
        # Pulse one real active day at a time; all values remain visible.
        x, y, _ = active_cells[(frame_index * 3) % len(active_cells)]
        pulse = (frame_index % 12) < 6
        if pulse:
            d.rounded_rectangle((x - 2, y - 2, x + cell + 2, y + cell + 2), radius=4, outline=theme["amber"], width=1)

    total = int(data["total_contributions"])
    active = int(data["active_days"])
    text_y = 238
    d.text((left, text_y), f"{total:,} contributions in the last year", font=font(11, "sansb"), fill=theme["text"])
    d.text((W / 2, text_y), f"{active} active days", font=font(10, "sans"), fill=theme["teal"], anchor="mt")
    legend_x = W - 180
    d.text((legend_x, text_y + 1), "LESS", font=font(7, "mono"), fill=theme["muted"])
    for i, col in enumerate(level_colours):
        rounded(d, (legend_x + 33 + i * 15, text_y - 1, legend_x + 44 + i * 15, text_y + 10), 2, col)
    d.text((legend_x + 113, text_y + 1), "MORE", font=font(7, "mono"), fill=theme["muted"])
    return im


def stats_picture(kind: str, width: str = "49%") -> str:
    if kind == "stats":
        dark, light = "github-profile-stats-dark.gif", "github-profile-stats-light.gif"
        alt = "Animated GitHub contribution metrics generated from one local data snapshot"
    else:
        dark, light = "technical-toolkit-dark.gif", "technical-toolkit-light.gif"
        alt = "Animated resume-aligned programming languages and AI toolkit"
    return (f'<picture><source media="(prefers-color-scheme: dark)" srcset="./assets/animated/{dark}" />'
            f'<source media="(prefers-color-scheme: light)" srcset="./assets/animated/{light}" />'
            f'<img src="./assets/animated/{dark}" width="{width}" alt="{alt}" /></picture>')


def heatmap_picture() -> str:
    return ('<picture><source media="(prefers-color-scheme: dark)" srcset="./assets/animated/annual-heatmap-dark.gif" />'
            '<source media="(prefers-color-scheme: light)" srcset="./assets/animated/annual-heatmap-light.gif" />'
            '<img src="./assets/animated/annual-heatmap-dark.gif" width="100%" alt="Animated full-width annual GitHub contribution heatmap for anshumanarchit-crypto" /></picture>')


def patch_readme(text: str) -> tuple[str, dict[str, int]]:
    counts = {"stats": 0, "toolkit": 0, "heatmap": 0}
    picture_re = re.compile(r"<picture\b[^>]*>.*?</picture>", re.IGNORECASE | re.DOTALL)

    def replace_stats(match: re.Match[str]) -> str:
        block = match.group(0)
        decoded = html.unescape(block).lower()
        is_remote = "github-readme-stats.vercel.app" in decoded
        is_stats_alt = "archit anshuman github statistics" in decoded or "github statistics" in decoded
        is_language_alt = "most-used programming languages" in decoded or "top languages" in decoded
        is_top_langs = "/top-langs/" in decoded or "top-langs" in decoded
        is_contribution_stats = ("stats.svg" in decoded or "contribution-stats" in decoded) and ("contribution statistics" in decoded or "monthly activity chart" in decoded or "contribution totals, streak" in decoded)
        if is_top_langs or is_language_alt:
            counts["toolkit"] += 1
            return stats_picture("toolkit")
        if is_contribution_stats:
            return contribution_stats_picture()
        if not (is_remote or is_stats_alt):
            return block
        if "github-readme-stats" in decoded or is_stats_alt:
            counts["stats"] += 1
            return stats_picture("stats")
        return block

    text = picture_re.sub(replace_stats, text)

    # Fallback for standalone remote img tags not wrapped in <picture>.
    img_re = re.compile(r"<img\b[^>]*>", re.IGNORECASE | re.DOTALL)
    def replace_standalone_stats(match: re.Match[str]) -> str:
        tag = html.unescape(match.group(0)).lower()
        if "stats.svg" in tag and ("contribution statistics" in tag or "monthly activity chart" in tag):
            return contribution_stats_picture()
        if "github-readme-stats.vercel.app" not in tag:
            return match.group(0)
        if "/top-langs/" in tag or "most-used programming languages" in tag:
            counts["toolkit"] += 1
            return stats_picture("toolkit")
        counts["stats"] += 1
        return stats_picture("stats")
    text = img_re.sub(replace_standalone_stats, text)

    # If the old external cards are already absent in this README revision,
    # insert the self-hosted equivalents directly below the existing overview
    # card so the Developer Stats section still matches the reference layout.
    lower_text = html.unescape(text).lower()
    has_stats_card = "github-profile-stats-dark.gif" in lower_text
    has_toolkit_card = "technical-toolkit-dark.gif" in lower_text
    if not (has_stats_card and has_toolkit_card):
        missing_cards = []
        if not has_stats_card:
            missing_cards.append(stats_picture("stats"))
            counts["stats"] += 1
        if not has_toolkit_card:
            missing_cards.append(stats_picture("toolkit"))
            counts["toolkit"] += 1
        insertion = "\n<p align=\"center\">\n  " + "\n  ".join(missing_cards) + "\n</p>\n"
        overview_match = None
        for match in picture_re.finditer(text):
            block_low = html.unescape(match.group(0)).lower()
            if "developer-overview-dark.gif" in block_low or "developer-overview-light.gif" in block_low:
                overview_match = match
                break
        if overview_match:
            at = overview_match.end()
            # The picture is usually inside a centered <p>; insert after that
            # paragraph closes, not inside it, to keep the README HTML valid.
            close_p = re.match(r"\s*</p\s*>", text[at:], re.IGNORECASE)
            if close_p:
                at += close_p.end()
            text = text[:at] + insertion + text[at:]
        else:
            heading_match = None
            for match in picture_re.finditer(text):
                if "section-developer-stats-accent" in html.unescape(match.group(0)).lower():
                    heading_match = match
                    break
            if heading_match:
                at = heading_match.end()
                close_p = re.match(r"\s*</p\s*>", text[at:], re.IGNORECASE)
                if close_p:
                    at += close_p.end()
                text = text[:at] + insertion + text[at:]
            else:
                print("WARNING: No developer-overview/header anchor found; generated cards but did not insert them into README.")

    def replace_heatmap_picture(match: re.Match[str]) -> str:
        block = match.group(0)
        low = html.unescape(block).lower()
        if any(key in low for key in ("contrib-heatmap.svg", "contrib-heatmap-light.svg", "annual-heatmap-dark.gif", "annual-heatmap-light.gif", "annual contribution heatmap")):
            counts["heatmap"] += 1
            return heatmap_picture()
        return block
    text = picture_re.sub(replace_heatmap_picture, text)

    # Markdown image fallback, if a repository has a bare Markdown heatmap image.
    md_re = re.compile(r"!\[([^\]]*(?:annual|contribution)[^\]]*heatmap[^\]]*)\]\(([^)]+)\)", re.IGNORECASE)
    text, md_count = md_re.subn(lambda m: heatmap_picture(), text)
    counts["heatmap"] += md_count

    # Standalone image fallback for a heatmap that is not wrapped in <picture>.
    # Protect complete picture blocks first so their nested <img> fallback is not
    # accidentally replaced a second time (which would create invalid nesting).
    protected: list[str] = []
    def protect_picture(match: re.Match[str]) -> str:
        token = f"__PROTECTED_PICTURE_{len(protected)}__"
        protected.append(match.group(0))
        return token
    masked = picture_re.sub(protect_picture, text)
    def replace_standalone_heatmap(match: re.Match[str]) -> str:
        tag = html.unescape(match.group(0)).lower()
        if "contrib-heatmap.svg" in tag or "annual-heatmap" in tag:
            counts["heatmap"] += 1
            return heatmap_picture()
        return match.group(0)
    masked = img_re.sub(replace_standalone_heatmap, masked)
    for i, block in enumerate(protected):
        masked = masked.replace(f"__PROTECTED_PICTURE_{i}__", block)
    text = masked
    return text, counts


def ensure_pillow_requirement(path: Path) -> str:
    """The local stats renderer depends on Pillow; add it only if absent."""
    if not path.exists():
        path.write_text("Pillow>=10.0\n", encoding="utf-8", newline="\n")
        return "Created scripts/requirements.txt with Pillow."
    original = path.read_text(encoding="utf-8")
    if re.search(r"(?im)^\s*pillow\s*([<=>!~]|$)", original):
        return "Pillow is already listed in scripts/requirements.txt."
    newline = "" if not original or original.endswith(("\n", "\r")) else "\n"
    path.write_text(original + newline + "Pillow>=10.0\n", encoding="utf-8", newline="\n")
    return "Added Pillow to scripts/requirements.txt for GitHub Actions."


def patch_workflow(path: Path) -> str:
    if not path.exists():
        return "Workflow not found; the new assets can still be generated manually."
    original = path.read_text(encoding="utf-8")
    text = original
    command = "python scripts/fix_developer_stats_heatmap.py"
    if command not in text:
        # Insert immediately before the commit action so assets are generated after fetch/render.
        commit_match = re.search(r"(?mi)^(\s*)- name: Commit\b", text)
        if commit_match:
            indent = commit_match.group(1)
            step = (f"{indent}- name: Refresh local developer stats and full-width heatmap\n"
                    f"{indent}  run: python scripts/fix_developer_stats_heatmap.py\n\n")
            text = text[:commit_match.start()] + step + text[commit_match.start():]
        else:
            return "Workflow exists, but no recognizable commit step was found; add the generator step before the commit action manually."
    # Extend file_pattern so the workflow commits the generated local animations.
    pattern_line = re.compile(r'(?m)^(\s*file_pattern:\s*)(["\'])(.*?)(\2)\s*$')
    def extend_pattern(match: re.Match[str]) -> str:
        content = match.group(3)
        needed = [
            "assets/animated/developer-overview-*.gif",
            "assets/animated/activity-graph-*.gif",
            "assets/animated/github-profile-stats-*.gif",
            "assets/animated/contribution-stats-*.gif",
            "assets/animated/technical-toolkit-*.gif",
            "assets/animated/annual-heatmap-*.gif",
            "README.md",
        ]
        for item in needed:
            if item not in content:
                content += " " + item
        return f"{match.group(1)}{match.group(2)}{content}{match.group(4)}"
    text = pattern_line.sub(extend_pattern, text)
    if text != original:
        path.write_text(text, encoding="utf-8", newline="\n")
        return "Updated the existing workflow to regenerate and commit only these stats/heatmap assets."
    return "Workflow already contains the generator step."


def main() -> int:
    try:
        data = parse_snapshot(DATA_PATH)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    frames = 42
    for name, palette in THEMES.items():
        # Refresh existing contribution-section animations from the same JSON too,
        # preventing old totals in the overview/activity graph from disagreeing.
        save_loop([draw_overview_card(palette, data, i, frames) for i in range(frames)], ASSET_DIR / f"developer-overview-{name}.gif", 95)
        save_loop([draw_activity_graph(palette, data, i, frames) for i in range(frames)], ASSET_DIR / f"activity-graph-{name}.gif", 95)
        save_loop([draw_stats_card(palette, data, i, frames) for i in range(frames)], ASSET_DIR / f"github-profile-stats-{name}.gif", 95)
        save_loop([draw_contribution_detail_card(palette, data, i, frames) for i in range(frames)], ASSET_DIR / f"contribution-stats-{name}.gif", 95)
        save_loop([draw_toolkit_card(palette, i, frames) for i in range(frames)], ASSET_DIR / f"technical-toolkit-{name}.gif", 95)
        save_loop([draw_heatmap(palette, data, i, frames) for i in range(frames)], ASSET_DIR / f"annual-heatmap-{name}.gif", 100)

    if not README_PATH.exists():
        print("WARNING: README.md not found; generated GIFs only.")
        counts = {"stats": 0, "toolkit": 0, "heatmap": 0}
    else:
        original = README_PATH.read_text(encoding="utf-8-sig")
        updated, counts = patch_readme(original)
        if updated != original:
            README_PATH.write_text(updated, encoding="utf-8", newline="\n")
        else:
            print("WARNING: README did not contain a recognized stats or heatmap reference; no README section was changed.")
    requirements_msg = ensure_pillow_requirement(ROOT / "scripts" / "requirements.txt")
    workflow_msg = patch_workflow(ROOT / ".github" / "workflows" / "update-profile-art.yml")

    # Ensure only the expected output assets are required for a successful run.
    expected = [
        ASSET_DIR / "github-profile-stats-dark.gif", ASSET_DIR / "github-profile-stats-light.gif",
        ASSET_DIR / "contribution-stats-dark.gif", ASSET_DIR / "contribution-stats-light.gif",
        ASSET_DIR / "technical-toolkit-dark.gif", ASSET_DIR / "technical-toolkit-light.gif",
        ASSET_DIR / "annual-heatmap-dark.gif", ASSET_DIR / "annual-heatmap-light.gif",
        ASSET_DIR / "developer-overview-dark.gif", ASSET_DIR / "developer-overview-light.gif",
        ASSET_DIR / "activity-graph-dark.gif", ASSET_DIR / "activity-graph-light.gif",
    ]
    missing = [str(p.relative_to(ROOT)) for p in expected if not p.exists() or p.stat().st_size == 0]
    if missing:
        print("ERROR: generated assets missing: " + ", ".join(missing), file=sys.stderr)
        return 3
    print("Contribution snapshot:", data.get("total_contributions"), "contributions /", data.get("active_days"), "active days")
    print("README updates:", counts)
    print("Generated and verified 12 looping GIF assets from the same contribution snapshot.")
    print(requirements_msg)
    print(workflow_msg)
    print("Done. The script did not modify contribution source data or unrelated README sections.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
