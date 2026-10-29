#!/usr/bin/env python3
"""Render theme-aware, looping profile graphics for Archit Anshuman.

All text and figures are rasterized into GIF frames, so the animation actually loops
on GitHub README pages. The heatmap alone is transparent outside its contribution cells.
Usage: python scripts/render_profile_motion_assets.py
"""
from __future__ import annotations

import datetime as dt
import json
import math
import os
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "contributions.json"
OUT = ROOT / "assets" / "animated"

THEMES = {
    "dark": {
        "bg0": "#07111F", "bg1": "#12263C", "bg2": "#193550", "tile": "#13283D",
        "tile2": "#182F47", "frame": "#2B4D68", "ink": "#EDF7FF", "muted": "#91A8C0",
        "dim": "#607D98", "track": "#243F56", "cyan": "#22D3EE", "teal": "#2DD4BF",
        "blue": "#60A5FA", "green": "#34D399", "amber": "#FBBF24", "violet": "#A78BFA",
        "pink": "#F472B6", "heat0": "#1A2A3C", "heat1": "#174A46", "heat2": "#147C70",
        "heat3": "#1EB7A6", "heat4": "#5BE7D6", "transparent": (0, 0, 0, 0),
    },
    "light": {
        "bg0": "#F8FBFF", "bg1": "#EEF5FC", "bg2": "#E3EEF9", "tile": "#FFFFFF",
        "tile2": "#F1F7FD", "frame": "#C7D8E8", "ink": "#10243A", "muted": "#4A627B",
        "dim": "#7D91A6", "track": "#DCE8F3", "cyan": "#0891B2", "teal": "#0F9E92",
        "blue": "#2563EB", "green": "#059669", "amber": "#B77908", "violet": "#7C3AED",
        "pink": "#DB2777", "heat0": "#E2EAF2", "heat1": "#BEEBE2", "heat2": "#75D9CA",
        "heat3": "#2CB8A7", "heat4": "#087F77", "transparent": (0, 0, 0, 0),
    },
}

ACHIEVEMENTS = [
    {
        "slug": "ai-for-bharat", "icon": "AI", "accent": "cyan", "eyebrow": "HACKATHON WINNER",
        "title": "AI for Bharat Hackathon", "subtitle": "HackerEarth  ·  Government of Karnataka",
        "result": "WINNER", "result_label": "AI FOR BHARAT",
    },
    {
        "slug": "global-academy-finalist", "icon": "GA", "accent": "blue", "eyebrow": "NATIONAL LEVEL HACKATHON",
        "title": "Global Academy", "subtitle": "National-level hackathon finalist",
        "result": "FINALIST", "result_label": "COMPETITION",
    },
    {
        "slug": "ai-build-challenge", "icon": "1ST", "accent": "amber", "eyebrow": "AI PRODUCT-BUILDING SPRINT",
        "title": "AI Build Challenge  ·  Bengaluru 2026",
        "subtitle": "Team Lead  ·  Hackingly × Masters' Union Ventures  ·  Qualcomm",
        "result": "1st RUNNER-UP", "result_label": "TEAM LEAD",
    },
    {
        "slug": "hackerrank-orchestrate-rank", "icon": "#", "accent": "green", "eyebrow": "HACKERRANK ORCHESTRATE",
        "title": "Competitive Coding Challenge", "subtitle": "HackerRank Orchestrate placement",
        "result": "RANK 418", "result_label": "HACKERRANK",
    },
    {
        "slug": "hackerrank-mysql-five-star", "icon": "SQL", "accent": "violet", "eyebrow": "DATABASE SKILL BADGE",
        "title": "MySQL  ·  HackerRank", "subtitle": "Five-star SQL proficiency badge",
        "result": "5 STARS", "result_label": "MYSQL",
    },
    {
        "slug": "additional-hackathons", "icon": "+3", "accent": "pink", "eyebrow": "COMMUNITY BUILDING",
        "title": "Hackathon Participant", "subtitle": "Bangalore Tech Summit Developer Challenge  ·  KJU  ·  Hack-A-League 4.0",
        "result": "3 EVENTS", "result_label": "PARTICIPATION",
    },
]


def _font_paths(bold: bool = False) -> list[str]:
    names = [
        r"C:\Windows\Fonts\segoeuib.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf",
        r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
    ]
    return names


def font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    for path in _font_paths(bold):
        if os.path.isfile(path):
            try:
                return ImageFont.truetype(path, size=size)
            except OSError:
                pass
    return ImageFont.load_default()


def hex_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[i:i+2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def blend(a: str, b: str, amount: float) -> tuple[int, int, int]:
    x, y = hex_rgb(a), hex_rgb(b)
    amount = max(0.0, min(1.0, amount))
    return tuple(round(x[i] * (1.0 - amount) + y[i] * amount) for i in range(3))  # type: ignore[return-value]


def gradient_image(width: int, height: int, c1: str, c2: str, radius: int = 0) -> Image.Image:
    img = Image.new("RGB", (width, height), c1)
    draw = ImageDraw.Draw(img)
    for x in range(width):
        color = blend(c1, c2, x / max(1, width - 1))
        draw.line((x, 0, x, height), fill=color)
    if radius:
        mask = Image.new("L", (width, height), 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, width - 1, height - 1), radius=radius, fill=255)
        rounded = Image.new("RGB", (width, height), hex_rgb(c1))
        rounded.paste(img, mask=mask)
        return rounded
    return img


def fit_font(draw: ImageDraw.ImageDraw, text: str, max_width: int, size: int, bold: bool = True, min_size: int = 12) -> ImageFont.ImageFont:
    while size > min_size:
        f = font(size, bold)
        if draw.textbbox((0, 0), text, font=f)[2] <= max_width:
            return f
        size -= 1
    return font(min_size, bold)


def center_text(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, f: ImageFont.ImageFont, fill: str) -> None:
    box = draw.textbbox((0, 0), text, font=f)
    w, h = box[2] - box[0], box[3] - box[1]
    draw.text((xy[0] - w / 2, xy[1] - h / 2 - box[1]), text, font=f, fill=fill)


def wrap_words(draw: ImageDraw.ImageDraw, text: str, f: ImageFont.ImageFont, max_width: int) -> list[str]:
    words, lines, current = text.split(), [], ""
    for word in words:
        test = f"{current} {word}".strip()
        if current and draw.textbbox((0, 0), test, font=f)[2] > max_width:
            lines.append(current)
            current = word
        else:
            current = test
    if current:
        lines.append(current)
    return lines


def gif_palettize(frame: Image.Image, transparent: bool = False) -> Image.Image:
    rgba = frame.convert("RGBA")
    if not transparent:
        return rgba.convert("RGB").quantize(colors=192, method=Image.Quantize.MEDIANCUT)
    alpha = rgba.getchannel("A")
    # Drop alpha without blending against magenta; transparent pixels are reassigned
    # to the reserved index below, avoiding colored fringes around the cells.
    rgb = rgba.convert("RGB")
    pal = rgb.quantize(colors=255, method=Image.Quantize.MEDIANCUT)
    palette = pal.getpalette() or [0] * 768
    if len(palette) < 768:
        palette += [0] * (768 - len(palette))
    palette[765:768] = [255, 0, 255]
    pal.putpalette(palette)
    transparent_mask = alpha.point(lambda a: 255 if a < 16 else 0)
    pal.paste(255, mask=transparent_mask)
    pal.info["transparency"] = 255
    return pal


def save_gif(frames: list[Image.Image], path: Path, duration: int = 90, transparent: bool = False) -> None:
    if not frames:
        raise ValueError(f"No frames provided for {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    paletted = [gif_palettize(frame, transparent=transparent) for frame in frames]
    kwargs = dict(save_all=True, append_images=paletted[1:], duration=duration, loop=0, optimize=True, disposal=2)
    if transparent:
        kwargs["transparency"] = 255
        kwargs["background"] = 255
    paletted[0].save(path, **kwargs)


def rounded_outline(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], radius: int, outline: str, width: int = 1) -> None:
    draw.rounded_rectangle(box, radius=radius, outline=outline, width=width)


def achievement_frames(item: dict, theme_name: str) -> list[Image.Image]:
    t = THEMES[theme_name]
    accent = t[item["accent"]]
    W, H, N = 1120, 206, 22
    base = gradient_image(W, H, t["bg0"], t["bg1"], radius=20)
    d = ImageDraw.Draw(base)
    d.rounded_rectangle((1, 1, W - 2, H - 2), radius=19, outline=t["frame"], width=2)
    d.rounded_rectangle((0, 0, 10, H), radius=5, fill=accent)
    # Quiet circuit-style geometry and corner nodes add depth without visual clutter.
    for i in range(8):
        x = 390 + i * 62
        d.line((x, 18, x + 40, 18), fill=blend(t["bg1"], accent, 0.11), width=1)
        d.ellipse((x + 37, 15, x + 43, 21), fill=blend(t["bg1"], accent, 0.23))
    d.line((32, 173, W - 30, 173), fill=t["track"], width=2)
    d.line((32, 185, W - 30, 185), fill=blend(t["bg1"], accent, 0.12), width=1)
    # Icon medallion.
    cx, cy = 88, 91
    d.ellipse((cx - 43, cy - 43, cx + 43, cy + 43), fill=t["tile"], outline=blend(t["bg1"], accent, 0.48), width=2)
    d.ellipse((cx - 34, cy - 34, cx + 34, cy + 34), outline=accent, width=2)
    center_text(d, (cx, cy), item["icon"], fit_font(d, item["icon"], 58, 23, True, 15), accent)
    # Card copy.
    d.text((157, 37), item["eyebrow"], font=font(13, True), fill=accent)
    d.text((157, 61), item["title"], font=fit_font(d, item["title"], 660, 27, True, 19), fill=t["ink"])
    subtitle_font = fit_font(d, item["subtitle"], 665, 16, False, 13)
    subtitle_lines = wrap_words(d, item["subtitle"], subtitle_font, 660)
    for line_index, line in enumerate(subtitle_lines[:2]):
        d.text((158, 105 + line_index * 23), line, font=subtitle_font, fill=t["muted"])
    # Result panel.
    panel_left = 868
    d.line((panel_left, 28, panel_left, 157), fill=t["frame"], width=2)
    d.rounded_rectangle((panel_left + 19, 37, W - 25, 150), radius=13, fill=t["tile"], outline=blend(t["frame"], accent, 0.35), width=1)
    result_f = fit_font(d, item["result"], W - panel_left - 60, 27, True, 16)
    center_text(d, (panel_left + 19 + (W - 25 - panel_left - 19) // 2, 77), item["result"], result_f, accent)
    center_text(d, (panel_left + 19 + (W - 25 - panel_left - 19) // 2, 113), item["result_label"], font(11, True), t["muted"])
    frames: list[Image.Image] = []
    for k in range(N):
        fr = base.copy()
        dr = ImageDraw.Draw(fr)
        progress = k / (N - 1)
        # Sweep runs over a slim track; the moving dot creates a clear but restrained loop.
        line_x = 34 + int((W - 74) * progress)
        glow_left = max(34, line_x - 76)
        glow_right = min(W - 35, line_x + 76)
        dr.line((glow_left, 173, glow_right, 173), fill=accent, width=3)
        dr.ellipse((line_x - 5, 168, line_x + 5, 178), fill=accent)
        # Gentle breathing ring around the card's icon.
        pulse = int(2 + 3 * (0.5 + 0.5 * math.sin((k / N) * 2 * math.pi)))
        dr.ellipse((88 - 44 - pulse, 91 - 44 - pulse, 88 + 44 + pulse, 91 + 44 + pulse), outline=blend(t["bg1"], accent, 0.6), width=1)
        # Traveling signal dot along the header circuitry.
        dot_x = 500 + int(420 * progress)
        dr.ellipse((dot_x - 3, 14, dot_x + 3, 20), fill=accent)
        frames.append(fr)
    return frames


def leadership_frames(theme_name: str) -> list[Image.Image]:
    t = THEMES[theme_name]
    W, H, N = 1200, 294, 26
    base = gradient_image(W, H, t["bg0"], t["bg1"], radius=22)
    d = ImageDraw.Draw(base)
    d.rounded_rectangle((1, 1, W - 2, H - 2), radius=21, outline=t["frame"], width=2)
    d.rounded_rectangle((0, 0, 9, H), radius=4, fill=t["cyan"])
    # Low contrast mesh lines and small nodes.
    for x in range(420, 640, 34):
        d.line((x, 20, x + 54, H - 24), fill=blend(t["bg1"], t["cyan"], 0.08), width=1)
    d.text((46, 30), "CAMPUS LEADERSHIP  /  01", font=font(13, True), fill=t["cyan"])
    d.text((44, 58), "CORE TEAM MEMBER", font=font(36, True), fill=t["ink"])
    d.text((47, 111), "TECH CLUB  ·  DR. AMBEDKAR INSTITUTE OF TECHNOLOGY", font=fit_font(d, "TECH CLUB  ·  DR. AMBEDKAR INSTITUTE OF TECHNOLOGY", 550, 15, True, 12), fill=t["muted"])
    d.text((47, 135), "CENTRALIZED CLUB PORTAL  ·  EVENT REGISTRATION + RESOURCES", font=fit_font(d, "CENTRALIZED CLUB PORTAL  ·  EVENT REGISTRATION + RESOURCES", 550, 12, True, 10), fill=t["muted"])
    d.line((47, 158, 582, 158), fill=t["frame"], width=2)
    tags = ["AI + FULL-STACK", "CODING SPRINTS", "PEER MENTORING"]
    tag_x = 47
    for tag in tags:
        f = font(11, True)
        w = d.textbbox((0, 0), tag, font=f)[2] + 22
        d.rounded_rectangle((tag_x, 174, tag_x + w, 206), radius=10, fill=t["tile"], outline=blend(t["frame"], t["cyan"], 0.35), width=1)
        d.text((tag_x + 11, 184), tag, font=f, fill=t["ink"])
        tag_x += w + 9
    # Three visual impact panels at the right.
    cards = [
        (635, 28, 798, 254, "500+", "STUDENTS", "EVENTS + RESOURCES", t["teal"]),
        (813, 28, 976, 254, "AI", "FULL-STACK", "BUILD SPRINTS", t["blue"]),
        (991, 28, 1165, 254, "TEAM", "MENTORING", "COMMUNITY", t["amber"]),
    ]
    for x1, y1, x2, y2, metric, label, sublabel, accent in cards:
        d.rounded_rectangle((x1, y1, x2, y2), radius=15, fill=t["tile"], outline=blend(t["frame"], accent, 0.42), width=2)
        d.rounded_rectangle((x1, y1, x1 + 5, y2), radius=2, fill=accent)
        center_text(d, ((x1 + x2) // 2, 91), metric, fit_font(d, metric, x2 - x1 - 22, 31, True, 20), accent)
        center_text(d, ((x1 + x2) // 2, 139), label, fit_font(d, label, x2 - x1 - 20, 13, True, 10), t["ink"])
        center_text(d, ((x1 + x2) // 2, 176), sublabel, fit_font(d, sublabel, x2 - x1 - 18, 10, True, 9), t["muted"])
        d.line((x1 + 16, 212, x2 - 16, 212), fill=t["track"], width=2)
    frames = []
    for k in range(N):
        fr = base.copy()
        dr = ImageDraw.Draw(fr)
        progress = k / (N - 1)
        start_x = 46 + int(515 * progress)
        dr.line((46, 226, start_x, 226), fill=t["cyan"], width=3)
        dr.ellipse((start_x - 5, 221, start_x + 5, 231), fill=t["cyan"])
        # Moving light travels across the three metric panels, reinforcing a continuous loop.
        px = 640 + int(500 * progress)
        dr.ellipse((px - 4, 18, px + 4, 26), fill=t["cyan"])
        # Small pulse on 500+ panel.
        r = int(3 + 2 * (0.5 + 0.5 * math.sin(progress * math.pi * 2)))
        dr.ellipse((716 - r, 58 - r, 716 + r, 58 + r), outline=t["teal"], width=1)
        frames.append(fr)
    return frames


def _heat_level(entry: dict) -> int:
    try:
        level = int(entry.get("level", -1))
    except (TypeError, ValueError):
        level = -1
    if 0 <= level <= 4:
        return level
    count = max(0, int(entry.get("count", 0)))
    return 0 if count == 0 else min(4, 1 + int(math.log2(count)))


def heatmap_frames(data: dict, theme_name: str) -> list[Image.Image]:
    t = THEMES[theme_name]
    entries = sorted(data.get("days", []), key=lambda item: item["date"])
    if not entries:
        raise ValueError("data/contributions.json contains no days for the heatmap")
    dates = [dt.date.fromisoformat(item["date"]) for item in entries]
    start_weekday = (dates[0].weekday() + 1) % 7
    locations = []
    for i, (entry, date) in enumerate(zip(entries, dates)):
        col = (i + start_weekday) // 7
        row = (date.weekday() + 1) % 7
        locations.append((col, row, _heat_level(entry), date))
    cols = max(col for col, _, _, _ in locations) + 1
    cell, gap = 13, 4
    left, top = 32, 36
    W = left * 2 + cols * cell + (cols - 1) * gap
    H = top + 7 * cell + 6 * gap + 16
    # Month labels are on the transparent canvas; there is no blue panel behind the grid.
    month_at: dict[int, str] = {}
    previous = None
    for col, _row, _level, date in locations:
        key = (date.year, date.month)
        if key != previous:
            month_at[col] = date.strftime("%b")
            previous = key
    frames: list[Image.Image] = []
    ncols = 0
    # One new vertical column at a time, then hold the completed year briefly.
    stages = list(range(1, cols + 1)) + [cols] * 7 + list(range(cols - 1, 0, -2)) + [0] * 2
    for stage_index, visible_cols in enumerate(stages):
        frame = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(frame)
        for col, label in month_at.items():
            if col < visible_cols:
                d.text((left + col * (cell + gap), 8), label, font=font(10, True), fill=t["muted"])
        for col, row, level, date in locations:
            if col >= visible_cols:
                continue
            x = left + col * (cell + gap)
            y = top + row * (cell + gap)
            color = [t["heat0"], t["heat1"], t["heat2"], t["heat3"], t["heat4"]][level]
            d.rounded_rectangle((x, y, x + cell, y + cell), radius=3, fill=color)
            if col == visible_cols - 1:
                d.rounded_rectangle((x - 1, y - 1, x + cell + 1, y + cell + 1), radius=4, outline=t["cyan"], width=1)
        # Re-emit the most recent column in the loop tail to form a satisfying reset.
        frames.append(frame)
    return frames


def _format_number(value: float | int) -> str:
    if isinstance(value, float) and not value.is_integer():
        return f"{value:.1f}"
    return f"{int(round(value)):,}"


def stats_frames(data: dict, theme_name: str) -> list[Image.Image]:
    t = THEMES[theme_name]
    W, H, PAD, GAP = 920, 710, 22, 14
    title_h = 43
    tile_top, tile_h = 59, 101
    tile_w = (W - 2 * PAD - GAP) // 2
    row_gap = 12
    chart_y = tile_top + 3 * tile_h + 2 * row_gap + 18
    chart_h = H - chart_y - 20
    monthly = data.get("monthly", [])[-12:]
    if not monthly:
        raise ValueError("data/contributions.json contains no monthly activity")
    day_count = len(data.get("days", []))
    cur = data.get("current_streak", {})
    longest = data.get("longest_streak", {})
    best = data.get("best_day", {})
    best_date = dt.date.fromisoformat(best["date"]).strftime("%Y-%m-%d") if best.get("date") else "—"
    metrics = [
        ("current streak", int(cur.get("length", 0)), " days", cur.get("start", "—"), t["teal"]),
        ("longest streak", int(longest.get("length", 0)), " days", longest.get("start", "—"), t["blue"]),
        ("contributions", int(data.get("total_contributions", 0)), "", "in the last year", t["ink"]),
        ("active days", int(data.get("active_days", 0)), f" / {day_count}", "days in range", t["teal"]),
        ("best day", int(best.get("count", 0)), "", best_date, t["amber"]),
        ("avg / active day", float(data.get("avg_per_active_day", 0)), "", "contributions", t["violet"]),
    ]
    max_month = max(int(item.get("total", 0)) for item in monthly) or 1

    def draw_frame(revealed: int, counts: list[float | int | None], bar_count: int, bar_fraction: float,
                   erase_values: set[int] | None = None, shrink_fraction: float = 1.0) -> Image.Image:
        img = gradient_image(W, H, t["bg0"], t["bg1"], radius=18)
        d = ImageDraw.Draw(img)
        d.rounded_rectangle((1, 1, W - 2, H - 2), radius=17, outline=t["frame"], width=2)
        d.line((0, title_h, W, title_h), fill=t["frame"], width=1)
        for i, color in enumerate(("#F87171", "#FBBF24", "#34D399")):
            d.ellipse((PAD + i * 16, 15, PAD + i * 16 + 8, 23), fill=color)
        center_text(d, (W // 2, title_h // 2 + 1), "anshumanarchit-crypto  /  ./stats.sh", font(12, True), t["muted"])

        for i, (label, actual, suffix, caption, accent) in enumerate(metrics):
            if i >= revealed:
                continue
            col, row = i % 2, i // 2
            x = PAD + col * (tile_w + GAP)
            y = tile_top + row * (tile_h + row_gap)
            d.rounded_rectangle((x, y, x + tile_w, y + tile_h), radius=12, fill=t["tile"], outline=t["frame"], width=2)
            d.rounded_rectangle((x, y, x + 4, y + tile_h), radius=2, fill=accent)
            d.text((x + 18, y + 14), "$ " + label, font=font(15, True), fill=t["muted"])
            d.text((x + 18, y + 42), caption, font=font(10, False), fill=t["dim"])
            hide = erase_values is not None and i in erase_values
            value = counts[i] if i < len(counts) else None
            if value is not None and not hide:
                visible_suffix = suffix
                if label in ("current streak", "longest streak"):
                    visible_suffix = " day" if float(value) == 1 else " days"
                s = _format_number(value) + visible_suffix
                d.text((x + 18, y + 58), s, font=fit_font(d, s, tile_w - 34, 25, True, 16), fill=accent)
            # Tiny corner light gives tiles a restrained active-state shimmer.
            if i == revealed - 1:
                d.ellipse((x + tile_w - 17, y + 12, x + tile_w - 9, y + 20), fill=t["cyan"])

        # Chart frame remains clean and opaque; only the heatmap is transparent.
        d.rounded_rectangle((PAD, chart_y, W - PAD, chart_y + chart_h), radius=12, fill=t["tile"], outline=t["frame"], width=2)
        d.text((PAD + 18, chart_y + 14), "$ contributions / month", font=font(15, True), fill=t["muted"])
        plot_left, plot_right = PAD + 24, W - PAD - 24
        plot_top, plot_bottom = chart_y + 50, chart_y + chart_h - 37
        slot = (plot_right - plot_left) / len(monthly)
        bar_w = slot * 0.55
        for j, entry in enumerate(monthly):
            value = max(0, int(entry.get("total", 0)))
            bx = plot_left + j * slot + (slot - bar_w) / 2
            full_height = max(2, (plot_bottom - plot_top) * value / max_month)
            if j < bar_count:
                frac = shrink_fraction if shrink_fraction < 1 else (bar_fraction if j == bar_count - 1 else 1.0)
                h = max(1, int(full_height * frac))
                color = t["cyan"] if value == max_month and value else t["teal"]
                d.rounded_rectangle((int(bx), int(plot_bottom - h), int(bx + bar_w), int(plot_bottom)), radius=4, fill=color)
                if value == max_month and value and frac >= 0.85:
                    text = str(value)
                    center_text(d, (int(bx + bar_w / 2), int(plot_bottom - h - 11)), text, font(10, True), t["ink"])
            month = dt.date.fromisoformat(entry["month"] + "-01").strftime("%b")
            center_text(d, (int(bx + bar_w / 2), plot_bottom + 17), month, font(10, True), t["dim"])
        return img

    frames: list[Image.Image] = []
    # Cards enter in normal reading order: first row left-to-right, then each row.
    for reveal in range(1, 7):
        frames.append(draw_frame(reveal, [None] * 6, 0, 0.0))
    actuals = [m[1] for m in metrics]
    # Count values up, one tile at a time; earlier values stay visible.
    counts: list[float | int | None] = [None] * 6
    for tile_index, actual in enumerate(actuals):
        for tick in (0.18, 0.42, 0.68, 1.0):
            counts[tile_index] = round(actual * tick, 1) if isinstance(actual, float) and not actual.is_integer() else int(round(actual * tick))
            frames.append(draw_frame(6, counts.copy(), 0, 0.0))
    # Draw the monthly chart column-by-column, then hold the complete dashboard.
    for j in range(1, len(monthly) + 1):
        frames.append(draw_frame(6, counts.copy(), j, 0.65))
        frames.append(draw_frame(6, counts.copy(), j, 1.0))
    for _ in range(10):
        frames.append(draw_frame(6, counts.copy(), len(monthly), 1.0))
    # Values disappear by row order (left-to-right); chart bars then redraw from the start.
    for count_hidden in range(1, 7):
        frames.append(draw_frame(6, counts.copy(), len(monthly), 1.0, erase_values=set(range(count_hidden))))
    for step in range(5, -1, -1):
        frames.append(draw_frame(6, [None] * 6, step, 0.55 if step else 0.0))
    return frames


def render_all() -> None:
    if not DATA.is_file():
        raise FileNotFoundError(f"Required contribution snapshot not found: {DATA.relative_to(ROOT)}")
    data = json.loads(DATA.read_text(encoding="utf-8"))
    for field in ("days", "monthly", "total_contributions", "active_days", "current_streak", "longest_streak", "best_day", "avg_per_active_day"):
        if field not in data:
            raise ValueError(f"{DATA.relative_to(ROOT)} is missing required field: {field}")
    OUT.mkdir(parents=True, exist_ok=True)

    for theme in ("dark", "light"):
        for item in ACHIEVEMENTS:
            path = OUT / f"achievement-{item['slug']}-{theme}.gif"
            save_gif(achievement_frames(item, theme), path, duration=85)
            print(f"Wrote {path.relative_to(ROOT)} ({1120} x {206}; animated achievement card)")
        lead_path = OUT / f"leadership-tech-club-{theme}.gif"
        save_gif(leadership_frames(theme), lead_path, duration=90)
        print(f"Wrote {lead_path.relative_to(ROOT)} (1200 x 294; animated leadership banner)")
        heat_path = OUT / f"contribution-heatmap-column-reveal-{theme}.gif"
        save_gif(heatmap_frames(data, theme), heat_path, duration=80, transparent=True)
        print(f"Wrote {heat_path.relative_to(ROOT)} (transparent background; left-to-right column reveal)")
        stats_path = OUT / f"stats-card-loop-{theme}.gif"
        save_gif(stats_frames(data, theme), stats_path, duration=95)
        print(f"Wrote {stats_path.relative_to(ROOT)} (count-up, row-wise value reveal/hide, recurring bar redraw)")


if __name__ == "__main__":
    render_all()
