
#!/usr/bin/env python3
"""Safely polish Archit Anshuman's animated GitHub profile README.

Updates only existing section-heading and tagline picture blocks, plus
legacy portrait/stat image references. Does not alter prose, project
descriptions, contribution JSON, workflows, or custom banner GIFs.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parent
README = ROOT / "README.md"
ANIM = ROOT / "assets" / "animated"


# The order is intentional: detect the dedicated stats heading separately.
SECTION_ASSETS = {
    "developer-stats": "GitHub Developer Stats",
    "about": "01 — About",
    "contributions": "02 — Contributions",
    "leadership": "03 — Leadership Experience",
    "skills": "04 — Technical Skills",
    "projects": "05 — Featured Projects",
    "achievements": "06 — Achievements",
    "snake": "Contribution Snake",
}


ALT_PATTERNS = {
    "developer-stats": re.compile(
        r"\bdeveloper\s*stat(?:s|istics)\b", re.IGNORECASE
    ),
    "about": re.compile(
        r"\b01\s*[—–-]\s*about\b", re.IGNORECASE
    ),
    "contributions": re.compile(
        r"\b02\s*[—–-]\s*contributions\b", re.IGNORECASE
    ),
    "leadership": re.compile(
        r"\b03\s*[—–-]\s*leadership\s*experience\b",
        re.IGNORECASE,
    ),
    "skills": re.compile(
        r"\b04\s*[—–-]\s*technical\s*skills\b", re.IGNORECASE
    ),
    "projects": re.compile(
        r"\b05\s*[—–-]\s*featured\s*projects\b",
        re.IGNORECASE,
    ),
    "achievements": re.compile(
        r"\b06\s*[—–-]\s*achievements\b", re.IGNORECASE
    ),
    "snake": re.compile(
        r"\bcontribution\s*snake\b", re.IGNORECASE
    ),
}


# Match a paragraph containing one picture element.
PICTURE_P = re.compile(
    r"<p\b[^>]*>\s*<picture\b.*?</picture>\s*</p>",
    re.IGNORECASE | re.DOTALL,
)

ALT_RE = re.compile(
    r"\balt\s*=\s*[\"']([^\"']*)[\"']",
    re.IGNORECASE,
)


def section_stem(key: str) -> str:
    """Return the canonical animated heading asset basename."""
    return f"section-{key}-accent-loop"


def is_heading_block(block: str, key: str) -> bool:
    """Identify a heading by its local asset path or its alt text."""
    stem = section_stem(key)

    # The asset name is the most reliable identifier. It still matches
    # when a previous version changed the heading's alt text.
    if stem.casefold() in block.casefold():
        return True

    # Fall back to the text alternative for an older heading graphic.
    alts = ALT_RE.findall(block)
    alt_text = " ".join(alts)

    if key == "snake":
        # Avoid matching unrelated images merely mentioning a snake.
        return bool(ALT_PATTERNS[key].search(alt_text)) and (
            "section-snake" in block.casefold()
            or "section_snake" in block.casefold()
        )

    return bool(ALT_PATTERNS[key].search(alt_text))


def make_heading_block(key: str) -> str:
    """Build a theme-aware animated heading without changing its layout."""
    alt = SECTION_ASSETS[key]
    stem = section_stem(key)

    return (
        '<p align="center"><picture>'
        f'<source media="(prefers-color-scheme: dark)" '
        f'srcset="./assets/animated/{stem}-dark.gif" />'
        f'<source media="(prefers-color-scheme: light)" '
        f'srcset="./assets/animated/{stem}-light.gif" />'
        f'<img src="./assets/animated/{stem}-dark.gif" '
        f'width="100%" alt="{alt}" />'
        "</picture></p>"
    )


def replace_section_headers(
    text: str,
) -> tuple[str, dict[str, int]]:
    """Normalize the eight existing animated heading blocks."""
    counts = {key: 0 for key in SECTION_ASSETS}

    def replace_block(match: re.Match[str]) -> str:
        block = match.group(0)

        for key in SECTION_ASSETS:
            if not is_heading_block(block, key):
                continue

            # Replacing only a confirmed heading picture prevents changes
            # to project artwork or other descriptive images.
            counts[key] += 1
            return make_heading_block(key)

        return block

    updated = PICTURE_P.sub(replace_block, text)
    return updated, counts


def replace_tagline_block(text: str) -> tuple[str, int]:
    """Ensure the existing tagline uses colored dark/light GIF variants."""
    for match in PICTURE_P.finditer(text):
        block = match.group(0)

        is_tagline = (
            "profile-tagline" in block.casefold()
            or bool(
                re.search(
                    r"building\s+agentic\s+ai\s+workflows",
                    block,
                    re.IGNORECASE,
                )
            )
        )

        if not is_tagline:
            continue

        replacement = (
            '<p align="center"><picture>'
            '<source media="(prefers-color-scheme: dark)" '
            'srcset="./assets/animated/profile-tagline-dark.gif" />'
            '<source media="(prefers-color-scheme: light)" '
            'srcset="./assets/animated/profile-tagline-light.gif" />'
            '<img src="./assets/animated/profile-tagline-dark.gif" '
            'width="100%" '
            'alt="Building agentic AI workflows; engineering NLP '
            'automation pipelines; building explainable AI systems" />'
            "</picture></p>"
        )

        updated = (
            text[:match.start()]
            + replacement
            + text[match.end():]
        )
        return updated, 1

    return text, 0


def replace_legacy_portrait_stats_refs(
    text: str,
) -> tuple[str, int]:
    """Upgrade legacy root-level portrait/stats references if present."""
    pairs = [
        (
            'srcset="./profile-ascii.svg"',
            'srcset="./assets/animated/profile-photo-ascii-dark.gif"',
        ),
        (
            'srcset="./profile-ascii-light.svg"',
            'srcset="./assets/animated/profile-photo-ascii-light.gif"',
        ),
        (
            'src="./profile-ascii.svg"',
            'src="./assets/animated/profile-photo-ascii-dark.gif"',
        ),
        (
            'src="./profile-ascii-light.svg"',
            'src="./assets/animated/profile-photo-ascii-light.gif"',
        ),
        (
            'srcset="./stats.svg"',
            'srcset="./assets/animated/contribution-stats-dark.gif"',
        ),
        (
            'srcset="./stats-light.svg"',
            'srcset="./assets/animated/contribution-stats-light.gif"',
        ),
        (
            'src="./stats.svg"',
            'src="./assets/animated/contribution-stats-dark.gif"',
        ),
        (
            'src="./stats-light.svg"',
            'src="./assets/animated/contribution-stats-light.gif"',
        ),
    ]

    changes = 0

    for old, new in pairs:
        count = text.count(old)
        if count:
            text = text.replace(old, new)
            changes += count

    return text, changes


def local_image_references(
    text: str,
) -> tuple[int, list[str]]:
    """Return the unique local image paths and paths that do not exist."""
    urls: list[str] = []

    attr_re = re.compile(
        r"\b(?:src|srcset)\s*=\s*[\"']([^\"']+)[\"']",
        re.IGNORECASE,
    )

    for match in attr_re.finditer(text):
        raw = match.group(1).strip()

        # srcset may contain multiple candidates separated by commas.
        for item in raw.split(","):
            item = item.strip()
            if not item:
                continue

            url = item.split()[0]

            if not url.startswith("./"):
                continue

            relative = (
                url[2:]
                .split("?", 1)[0]
                .split("#", 1)[0]
            )

            if relative:
                urls.append(relative)

    unique = sorted(set(urls))
    missing = [
        path for path in unique
        if not (ROOT / path).is_file()
    ]

    return len(unique), missing


def validate_required_gifs() -> list[str]:
    """Check that every GIF this script references exists and loops."""
    required: set[Path] = set()

    for key in SECTION_ASSETS:
        stem = section_stem(key)
        required.add(ANIM / f"{stem}-dark.gif")
        required.add(ANIM / f"{stem}-light.gif")

    required.update({
        ANIM / "profile-tagline-dark.gif",
        ANIM / "profile-tagline-light.gif",
        ANIM / "project-urjanetra-dark.gif",
        ANIM / "project-urjanetra-light.gif",
        ANIM / "project-ayuscout-dark.gif",
        ANIM / "project-ayuscout-light.gif",
        ANIM / "profile-photo-ascii-dark.gif",
        ANIM / "profile-photo-ascii-light.gif",
        ANIM / "contribution-stats-dark.gif",
        ANIM / "contribution-stats-light.gif",
    })

    for slug in (
        "ai-for-bharat",
        "ai-build-challenge",
        "global-academy-finalist",
        "hackerrank-orchestrate-rank",
        "hackerrank-mysql-five-star",
    ):
        for theme in ("dark", "light"):
            required.add(
                ANIM / f"achievement-{slug}-{theme}.gif"
            )

    errors: list[str] = []

    for path in sorted(required):
        if not path.is_file():
            errors.append(f"Missing GIF: {path.relative_to(ROOT)}")
            continue

        try:
            with Image.open(path) as image:
                frame_count = getattr(image, "n_frames", 1)
                loop_count = image.info.get("loop")

                if frame_count < 2:
                    errors.append(
                        f"Not animated (fewer than 2 frames): "
                        f"{path.relative_to(ROOT)}"
                    )

                if loop_count != 0:
                    errors.append(
                        f"GIF does not declare infinite looping: "
                        f"{path.relative_to(ROOT)}"
                    )

        except Exception as exc:
            errors.append(
                f"Unreadable GIF {path.relative_to(ROOT)}: {exc}"
            )

    return errors


def main() -> int:
    if not README.is_file():
        print(
            "ERROR: README.md was not found beside this script. "
            "Run it from the repository root."
        )
        return 2

    original = README.read_text(encoding="utf-8")
    updated = original

    updated, heading_counts = replace_section_headers(updated)
    updated, tagline_count = replace_tagline_block(updated)
    updated, stats_ref_count = replace_legacy_portrait_stats_refs(updated)

    missing_headings = [
        key for key, count in heading_counts.items()
        if count == 0
    ]

    if missing_headings:
        print(
            "ERROR: Could not identify these heading blocks:",
            ", ".join(missing_headings),
        )
        print("No README changes were written.")
        print(
            "Detected heading blocks:",
            heading_counts,
        )
        return 3

    if tagline_count != 1:
        print(
            "ERROR: Expected exactly one tagline picture block; "
            f"found {tagline_count}. No README changes were written."
        )
        return 4

    gif_errors = validate_required_gifs()

    if gif_errors:
        print("ERROR: Required animation assets are missing or invalid:")
        for error in gif_errors:
            print(" -", error)
        print("No README changes were written.")
        return 5

    refs_count, missing_refs = local_image_references(updated)

    if missing_refs:
        print("ERROR: Local README image references are missing:")
        for path in missing_refs:
            print(" -", path)
        print("No README changes were written.")
        return 6

    # Write only after all validation passes.
    if updated != original:
        README.write_text(updated, encoding="utf-8", newline="\n")

    print("Profile visual polish completed successfully.")
    print("Heading blocks normalized:", heading_counts)
    print("Colored tagline block updated:", tagline_count)
    print("Legacy portrait/stats references changed:", stats_ref_count)
    print(
        f"Local image references checked: {refs_count}; missing: 0"
    )
    print("GIF validation passed: required assets are animated and loop.")
    print("Other README prose, projects, and section content were preserved.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
