#!/usr/bin/env python3
"""Apply only the requested leadership, achievements and contribution animation refinements.

This script leaves all other README sections and the contribution source JSON untouched.
Run it from the root of Archit's profile repository.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent
README = ROOT / "README.md"
ASSET_RENDERER = ROOT / "scripts" / "render_profile_motion_assets.py"

ACHIEVEMENT_CARDS = [
    ("ai-for-bharat", "Winner — AI for Bharat Hackathon"),
    ("global-academy-finalist", "Finalist — Global Academy National Level Hackathon"),
    ("ai-build-challenge", "1st Runner-Up, Team Lead — AI Build Challenge Bengaluru 2026"),
    ("hackerrank-orchestrate-rank", "Rank 418 — HackerRank Orchestrate"),
    ("hackerrank-mysql-five-star", "5-Star MySQL Badge — HackerRank"),
    ("additional-hackathons", "Participant — Bangalore Tech Summit Developer Challenge, KJU Hackathon, Hack-A-League 4.0"),
]


def animation_picture(path_stub: str, alt: str, width: str = "100%") -> str:
    dark = f"./assets/animated/{path_stub}-dark.gif"
    light = f"./assets/animated/{path_stub}-light.gif"
    return (
        '<p align="center">'
        '<picture>'
        f'<source media="(prefers-color-scheme: dark)" srcset="{dark}" />'
        f'<source media="(prefers-color-scheme: light)" srcset="{light}" />'
        f'<img src="{dark}" width="{width}" alt="{alt}" />'
        '</picture></p>'
    )


def achievement_block() -> str:
    return "\n\n".join(
        animation_picture(f"achievement-{slug}", alt)
        for slug, alt in ACHIEVEMENT_CARDS
    )


def find_picture_paragraph(text: str, predicate) -> re.Match[str] | None:
    for match in re.finditer(r"<p\b[^>]*>.*?</p>", text, flags=re.I | re.S):
        if predicate(match.group(0)):
            return match
    return None


def find_portrait_stats_block(text: str) -> re.Match[str] | None:
    # Original version uses a paragraph; subsequent patch versions may use a table.
    patterns = [r"<p\b[^>]*>.*?</p>", r"<table\b[^>]*>.*?</table>"]
    for pattern in patterns:
        for match in re.finditer(pattern, text, flags=re.I | re.S):
            block = match.group(0).lower()
            has_portrait = "profile-ascii" in block or "profile-photo-ascii" in block
            has_stats = any(token in block for token in ("stats.svg", "contribution-stats", "stats-card-loop"))
            if has_portrait and has_stats:
                return match
    return None


def update_portrait_stats(block: str) -> str:
    pics = list(re.finditer(r"<picture\b.*?</picture>", block, flags=re.I | re.S))
    portrait_match = next((m for m in pics if "profile-ascii" in m.group(0).lower() or "profile-photo-ascii" in m.group(0).lower()), None)
    if portrait_match is None:
        raise ValueError("Could not isolate the ASCII portrait picture in the contribution row.")
    portrait = portrait_match.group(0)
    # Size the portrait relative to its table cell instead of letting it force its own line.
    portrait = re.sub(r'(<img\b[^>]*?\bwidth\s*=\s*)["\'][^"\']*["\']', r'\1"100%"', portrait, count=1, flags=re.I)
    stats = (
        '<picture>'
        '<source media="(prefers-color-scheme: dark)" srcset="./assets/animated/stats-card-loop-dark.gif" />'
        '<source media="(prefers-color-scheme: light)" srcset="./assets/animated/stats-card-loop-light.gif" />'
        '<img src="./assets/animated/stats-card-loop-dark.gif" width="100%" alt="Looping contribution dashboard: metrics count up, disappear row-wise, and monthly bars redraw" />'
        '</picture>'
    )
    # A simple HTML table makes the two-column alignment reliable in GitHub's renderer.
    return (
        '<table width="100%" border="0" cellpadding="0" cellspacing="0">\n'
        '  <tr>\n'
        '    <td width="40%" align="center" valign="middle">' + portrait + '</td>\n'
        '    <td width="60%" align="center" valign="middle">' + stats + '</td>\n'
        '  </tr>\n'
        '</table>'
    )


def update_heatmap(text: str) -> tuple[str, int]:
    match = find_picture_paragraph(
        text,
        lambda block: any(key in block.lower() for key in ("contrib-heatmap", "contribution-heatmap-column-reveal", "annual-heatmap")),
    )
    if not match:
        raise ValueError("Could not locate the annual contribution heatmap image paragraph.")
    replacement = animation_picture(
        "contribution-heatmap-column-reveal",
        "Transparent annual contribution heatmap; cells reveal from left to right, one week column at a time",
    )
    return text[:match.start()] + replacement + text[match.end():], 1


def update_leadership(text: str) -> tuple[str, int]:
    # Replace only the prose from the Tech Club heading up to (but not including) Technical Skills.
    skills_matches = [m for m in re.finditer(r'<p\b[^>]*>.*?</p>', text, flags=re.I | re.S)
                      if "section-skills-accent-loop" in m.group(0).lower()]
    if len(skills_matches) != 1:
        raise ValueError(f"Expected one Technical Skills section banner; found {len(skills_matches)}.")
    skills = skills_matches[0]
    head = re.search(r"\*\*Core Team Member\s*[·|\-]\s*Tech Club, Dr\. AIT\*\*", text[:skills.start()], flags=re.I)
    replacement = animation_picture(
        "leadership-tech-club",
        "Animated Tech Club leadership banner: AI and full-stack coding sprints, peer mentoring, and a club portal used by 500+ students",
    )
    if head:
        # Only remove the explicit title and leadership bullets; preserve all sections around them.
        return text[:head.start()] + replacement + "\n\n" + text[skills.start():], 1
    # Idempotency: if the banner was already installed, leave that section intact.
    before_skills = text[:skills.start()]
    if "leadership-tech-club-dark.gif" in before_skills:
        return text, 0
    raise ValueError("Could not find the Core Team Member leadership text or its replacement banner.")


def update_achievements(text: str) -> tuple[str, int]:
    headers = [m for m in re.finditer(r'<p\b[^>]*>.*?</p>', text, flags=re.I | re.S)
               if "section-achievements-accent-loop" in m.group(0).lower()]
    snakes = [m for m in re.finditer(r'<p\b[^>]*>.*?</p>', text, flags=re.I | re.S)
              if "section-snake-accent-loop" in m.group(0).lower()]
    if len(headers) != 1 or len(snakes) != 1 or snakes[0].start() <= headers[0].end():
        raise ValueError("Could not locate the unique Achievements and Contribution Snake section boundaries.")
    replacement = "\n\n" + achievement_block() + "\n\n"
    return text[:headers[0].end()] + replacement + text[snakes[0].start():], 1


def local_refs(text: str) -> tuple[int, list[str]]:
    refs: set[str] = set()
    for match in re.finditer(r'\b(?:src|srcset)\s*=\s*["\']([^"\']+)["\']', text, flags=re.I):
        for candidate in match.group(1).split(","):
            candidate = candidate.strip()
            if not candidate:
                continue
            uri = candidate.split()[0].split("?", 1)[0].split("#", 1)[0]
            if uri.startswith("./"):
                refs.add(uri[2:])
    missing = sorted(item for item in refs if not (ROOT / item).is_file())
    return len(refs), missing


def validate_gifs() -> list[str]:
    expected = []
    for theme in ("dark", "light"):
        expected.extend([
            ROOT / "assets" / "animated" / f"leadership-tech-club-{theme}.gif",
            ROOT / "assets" / "animated" / f"contribution-heatmap-column-reveal-{theme}.gif",
            ROOT / "assets" / "animated" / f"stats-card-loop-{theme}.gif",
        ])
        expected.extend(ROOT / "assets" / "animated" / f"achievement-{slug}-{theme}.gif" for slug, _ in ACHIEVEMENT_CARDS)
    errors = []
    for path in expected:
        if not path.is_file():
            errors.append(f"Missing: {path.relative_to(ROOT)}")
            continue
        try:
            with Image.open(path) as image:
                if getattr(image, "n_frames", 1) < 2:
                    errors.append(f"Not animated: {path.relative_to(ROOT)}")
                if image.info.get("loop", 0) != 0:
                    errors.append(f"Not infinitely looping: {path.relative_to(ROOT)}")
        except Exception as exc:
            errors.append(f"Cannot open {path.relative_to(ROOT)}: {exc}")
    return errors


def main() -> int:
    if not README.is_file():
        print("ERROR: Run this script from the root of the profile repository; README.md was not found.")
        return 2
    if not (ROOT / "data" / "contributions.json").is_file():
        print("ERROR: data/contributions.json is missing. No README changes were made.")
        return 2
    if not ASSET_RENDERER.is_file():
        print("ERROR: scripts/render_profile_motion_assets.py is missing from the patch.")
        return 2

    # Generate theme pairs from this repo's own data before editing README.md.
    result = subprocess.run([sys.executable, str(ASSET_RENDERER)], cwd=ROOT, text=True)
    if result.returncode:
        print("ERROR: Asset generation failed; README.md has not been changed.")
        return result.returncode
    gif_errors = validate_gifs()
    if gif_errors:
        print("ERROR: Generated GIF validation failed:")
        for problem in gif_errors:
            print(" -", problem)
        print("README.md has not been changed.")
        return 3

    original = README.read_text(encoding="utf-8")
    updated = original
    try:
        updated, heatmap_count = update_heatmap(updated)
        # Update the portrait + stats row before section replacement.
        row = find_portrait_stats_block(updated)
        if not row:
            raise ValueError("Could not locate the combined ASCII portrait and contribution stats block.")
        updated = updated[:row.start()] + update_portrait_stats(row.group(0)) + updated[row.end():]
        updated, leadership_count = update_leadership(updated)
        updated, achievement_count = update_achievements(updated)
    except Exception as exc:
        print(f"ERROR: {exc}")
        print("README.md has not been changed. The generated assets remain available for inspection.")
        return 4

    count, missing = local_refs(updated)
    if missing:
        print("ERROR: Some local README image references do not resolve:")
        for ref in missing:
            print(" -", ref)
        print("README.md has not been changed.")
        return 5

    README.write_text(updated, encoding="utf-8", newline="\n")
    print(f"README updated: heatmap={heatmap_count}, leadership text replaced={leadership_count}, achievement section graphics={achievement_count}.")
    print(f"Local image references checked: {count}; missing: 0.")
    print("Only the contribution heatmap/stats row, Tech Club leadership body, and Achievements body were changed.")
    print("Review: git diff --check; git diff -- README.md; git status --short")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
