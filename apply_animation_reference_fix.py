#!/usr/bin/env python3
"""Wire the existing animated profile assets into README.md and restore animated SVG stats.

Run from the root of Archit's profile repository. This script preserves README prose,
project descriptions, URLs, contribution JSON and the profile banner files.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent
README = ROOT / "README.md"
ANIM = ROOT / "assets" / "animated"

PROJECTS = {
    "urjanetra": "UrjaNetra AI — energy supply-chain risk and forecasting",
    "ayuscout": "AyuScout AI — real-time patient safety signal detection",
}
ACHIEVEMENTS = [
    ("ai-for-bharat", "Winner — AI for Bharat Hackathon"),
    ("ai-build-challenge", "1st Runner-Up, Team Lead — AI Build Challenge Bengaluru 2026"),
    ("global-academy-finalist", "Finalist — Global Academy National Level Hackathon"),
    ("hackerrank-orchestrate-rank", "Rank 418 — HackerRank Orchestrate"),
    ("hackerrank-mysql-five-star", "5-Star MySQL Badge — HackerRank"),
]


def replace_exact(text: str, replacements: list[tuple[str, str]]) -> tuple[str, int]:
    total = 0
    for old, new in replacements:
        count = text.count(old)
        if count:
            text = text.replace(old, new)
            total += count
    return text, total


def picture(slug: str, alt: str, width: str = "100%") -> str:
    return (
        '<picture>'
        f'<source media="(prefers-color-scheme: dark)" srcset="./assets/animated/achievement-{slug}-dark.gif" />'
        f'<source media="(prefers-color-scheme: light)" srcset="./assets/animated/achievement-{slug}-light.gif" />'
        f'<img src="./assets/animated/achievement-{slug}-dark.gif" width="{width}" alt="{alt}" />'
        '</picture>'
    )


def animated_achievement_table() -> str:
    first = f'<td width="50%" valign="top">{picture(ACHIEVEMENTS[0][0], ACHIEVEMENTS[0][1])}</td>'
    second = f'<td width="50%" valign="top">{picture(ACHIEVEMENTS[1][0], ACHIEVEMENTS[1][1])}</td>'
    third = f'<td width="50%" valign="top">{picture(ACHIEVEMENTS[2][0], ACHIEVEMENTS[2][1])}</td>'
    fourth = f'<td width="50%" valign="top">{picture(ACHIEVEMENTS[3][0], ACHIEVEMENTS[3][1])}</td>'
    fifth = f'<td colspan="2" align="center" valign="top"><p align="center">{picture(ACHIEVEMENTS[4][0], ACHIEVEMENTS[4][1], "52%")}</p></td>'
    return (
        '<table width="100%">\n'
        '  <tr>\n    ' + first + '\n    ' + second + '\n  </tr>\n'
        '  <tr>\n    ' + third + '\n    ' + fourth + '\n  </tr>\n'
        '  <tr>\n    ' + fifth + '\n  </tr>\n'
        '</table>'
    )


def validate_asset_files() -> list[str]:
    required = []
    for slug in PROJECTS:
        required.extend([ANIM / f"project-{slug}-dark.gif", ANIM / f"project-{slug}-light.gif"])
    for slug, _ in ACHIEVEMENTS:
        required.extend([ANIM / f"achievement-{slug}-dark.gif", ANIM / f"achievement-{slug}-light.gif"])
    problems = []
    for path in required:
        if not path.is_file():
            problems.append(f"Missing animation asset: {path.relative_to(ROOT)}")
            continue
        try:
            with Image.open(path) as im:
                if getattr(im, "n_frames", 1) < 2:
                    problems.append(f"Not animated (fewer than two frames): {path.relative_to(ROOT)}")
                if im.info.get("loop", 0) != 0:
                    problems.append(f"GIF does not loop infinitely: {path.relative_to(ROOT)}")
        except Exception as exc:
            problems.append(f"Could not read {path.relative_to(ROOT)}: {exc}")
    return problems


def local_refs(text: str) -> tuple[int, list[str]]:
    refs: set[str] = set()
    for match in re.finditer(r'\b(?:src|srcset)\s*=\s*["\']([^"\']+)["\']', text, re.I):
        raw = match.group(1).strip()
        for item in raw.split(","):
            item = item.strip()
            if not item:
                continue
            uri = item.split()[0].split("?", 1)[0].split("#", 1)[0]
            if uri.startswith("./"):
                refs.add(uri[2:])
    missing = sorted(ref for ref in refs if not (ROOT / ref).is_file())
    return len(refs), missing


def main() -> int:
    if not README.is_file():
        print("ERROR: README.md was not found. Run this script from the profile repository root.")
        return 2
    data_file = ROOT / "data" / "contributions.json"
    if not data_file.is_file():
        print("ERROR: data/contributions.json was not found; stats SVGs were not regenerated.")
        return 2

    problems = validate_asset_files()
    if problems:
        print("ERROR: Animation assets failed validation:")
        for problem in problems:
            print(" -", problem)
        print("No README changes were written.")
        return 3

    original = README.read_text(encoding="utf-8")
    updated = original

    # Switch project cards from static SVGs to the already-committed looping GIFs.
    mapping = [
        ('srcset="./assets/project-urjanetra.svg"', 'srcset="./assets/animated/project-urjanetra-dark.gif"'),
        ('srcset="./assets/project-urjanetra-light.svg"', 'srcset="./assets/animated/project-urjanetra-light.gif"'),
        ('src="./assets/project-urjanetra.svg"', 'src="./assets/animated/project-urjanetra-dark.gif"'),
        ('src="./assets/project-ayuscout.svg"', 'src="./assets/animated/project-ayuscout-dark.gif"'),
        ('srcset="./assets/project-ayuscout.svg"', 'srcset="./assets/animated/project-ayuscout-dark.gif"'),
        ('srcset="./assets/project-ayuscout-light.svg"', 'srcset="./assets/animated/project-ayuscout-light.gif"'),
        ('src="./assets/project-ayuscout-light.svg"', 'src="./assets/animated/project-ayuscout-light.gif"'),
    ]
    # Add both direct dark and light variants; repeated source order is intentional and exact.
    updated, project_changes = replace_exact(updated, mapping)

    # Also replace already-existing older achievement SVG references in case the README
    # has not been wired to the newer looping card assets yet.
    for slug, _alt in ACHIEVEMENTS[:2]:
        for suffix in ("", "-light"):
            old = f'./assets/achievement-{slug}{suffix}.svg'
            theme = "light" if suffix else "dark"
            new = f'./assets/animated/achievement-{slug}-{theme}.gif'
            updated = updated.replace(f'srcset="{old}"', f'srcset="{new}"')
            updated = updated.replace(f'src="{old}"', f'src="{new}"')

    # The five cards already exist as looping GIFs. Replace only the achievement table
    # that contains the AI for Bharat card, preserving the surrounding prose and links.
    table_blocks = list(re.finditer(r'<table\b[^>]*>.*?</table>', updated, re.I | re.S))
    matching_tables = [m for m in table_blocks if "achievement-ai-for-bharat" in m.group(0)]
    table_match = matching_tables[0] if len(matching_tables) == 1 else None
    if not table_match:
        print("ERROR: Could not locate the achievement card table; no README changes were written.")
        print("Check that README.md still contains the AI for Bharat achievement table.")
        return 4
    updated = updated[:table_match.start()] + animated_achievement_table() + updated[table_match.end():]

    # The reference has portrait + stats side-by-side. Make the stats panel use the
    # same 49% width and use animated SVG count-up/bar-growth rather than the subtle GIF.
    all_picture_blocks = list(re.finditer(r'<picture\b.*?</picture>', updated, re.I | re.S))
    picture_matches = [m for m in all_picture_blocks if re.search(r'(?:contribution-stats-dark\.gif|(?:src|srcset)=["\']\./stats(?:-light)?\.svg)', m.group(0), re.I)]
    if len(picture_matches) != 1:
        print(f"ERROR: Expected one contribution stats picture block; found {len(picture_matches)}.")
        print("No README changes were written. Inspect the portrait/stats row before retrying.")
        return 5
    stats_picture = (
        '<picture>'
        '<source media="(prefers-color-scheme: dark)" srcset="./stats.svg?v=2" />'
        '<source media="(prefers-color-scheme: light)" srcset="./stats-light.svg?v=2" />'
        '<img src="./stats.svg?v=2" width="49%" alt="Animated contribution statistics with count-up metrics and growing monthly bars" />'
        '</picture>'
    )
    m = picture_matches[0]
    updated = updated[:m.start()] + stats_picture + updated[m.end():]

    # Fail early if expected animation targets weren't wired by the README's current format.
    for target in (
        "./assets/animated/project-urjanetra-dark.gif",
        "./assets/animated/project-urjanetra-light.gif",
        "./assets/animated/project-ayuscout-dark.gif",
        "./assets/animated/project-ayuscout-light.gif",
        "./assets/animated/achievement-ai-for-bharat-dark.gif",
        "./assets/animated/achievement-ai-build-challenge-dark.gif",
        "./assets/animated/achievement-global-academy-finalist-dark.gif",
        "./assets/animated/achievement-hackerrank-orchestrate-rank-dark.gif",
        "./assets/animated/achievement-hackerrank-mysql-five-star-dark.gif",
        'srcset="./stats.svg?v=2"', 'srcset="./stats-light.svg?v=2"',
    ):
        if target not in updated:
            print(f"ERROR: Expected animation reference not found after patch: {target}")
            print("No README changes were written.")
            return 6

    # Render two personalized, animated SVG cards from the user's current snapshot.
    renderer = ROOT / "scripts" / "render_animated_stats_svg.py"
    if not renderer.is_file():
        print("ERROR: scripts/render_animated_stats_svg.py is missing from the patch.")
        return 7
    for theme, output in (("dark", ROOT / "stats.svg"), ("light", ROOT / "stats-light.svg")):
        command = [sys.executable, str(renderer), "--theme", theme, "--input", str(data_file), "--output", str(output)]
        result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
        if result.returncode:
            print(result.stdout)
            print(result.stderr)
            print("ERROR: Could not render stats SVGs; README.md was not changed.")
            return result.returncode
        print(result.stdout.strip())

    count, missing = local_refs(updated)
    if missing:
        print("ERROR: README contains unresolved local image references:")
        for ref in missing:
            print(" -", ref)
        print("README.md was not changed. Fix missing local assets and retry.")
        return 8

    README.write_text(updated, encoding="utf-8", newline="\n")
    print(f"README animation references updated ({project_changes} project path replacements).")
    print(f"Local README image references checked: {count}; missing: 0.")
    print("Projects + all five achievement cards use looping GIFs; stats use count-up/bar-growth SVG animations.")
    print("Review with: git diff --check; git diff -- README.md stats.svg stats-light.svg")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
