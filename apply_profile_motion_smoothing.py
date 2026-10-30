#!/usr/bin/env python3
"""Refine Archit's existing profile animations without changing other README content.

Changes:
- widens the ASCII portrait cell to 40% (stats card 60%)
- removes moving horizontal sweep lines from generated achievement and Tech Club cards
- slows the newly generated animation families and existing animated GIFs
- cleans the moving underline/wave from existing project and AI Build Challenge banners

Run from the profile repository root after any Git rebase has completed.
Requires Pillow (already used by the existing motion asset generator).
"""
from __future__ import annotations

import re
import math
import subprocess
import sys
from pathlib import Path
from PIL import Image, ImageSequence, ImageChops, ImageDraw

ROOT = Path(__file__).resolve().parent
README = ROOT / "README.md"
UPDATER = ROOT / "apply_profile_motion_refinement.py"
RENDERER = ROOT / "scripts" / "render_profile_motion_assets.py"
ANIM = ROOT / "assets" / "animated"
MIN_DURATION_MS = 150


def patch_text_file(path: Path, replacements: list[tuple[str, str]], label: str) -> None:
    if not path.is_file():
        raise RuntimeError(f"Required file not found: {path.relative_to(ROOT)}")
    text = path.read_text(encoding="utf-8")
    original = text
    for old, new in replacements:
        if old in text:
            text = text.replace(old, new)
        elif new in text:
            # Already patched; make this safe to run again.
            continue
        else:
            raise RuntimeError(f"Could not find the expected source fragment in {path.relative_to(ROOT)}: {old[:90]!r}")
    if text != original:
        path.write_text(text, encoding="utf-8", newline="\n")
        print(f"Updated {path.relative_to(ROOT)} ({label}).")
    else:
        print(f"Already updated: {path.relative_to(ROOT)}.")


def patch_renderer() -> None:
    if not RENDERER.is_file():
        raise RuntimeError("scripts/render_profile_motion_assets.py is missing. Apply the Profile Motion Upgrade patch first.")
    text = RENDERER.read_text(encoding="utf-8")
    original = text

    # Remove the static progress tracks from the achievement card and its moving sweep/dot.
    text = text.replace(
        '    d.line((32, 173, W - 30, 173), fill=t["track"], width=2)\n'
        '    d.line((32, 185, W - 30, 185), fill=blend(t["bg1"], accent, 0.12), width=1)\n',
        "",
    )
    achievement_start = text.find("    frames: list[Image.Image] = []", text.find("def achievement_frames"))
    achievement_end = text.find("    return frames", achievement_start)
    if achievement_start < 0 or achievement_end < 0:
        raise RuntimeError("Could not locate the achievement animation loop in the existing renderer.")
    current_loop = text[achievement_start:achievement_end + len("    return frames")]
    if "Sweep runs over a slim track" in current_loop:
        new_loop = '''    frames: list[Image.Image] = []
    for k in range(N):
        fr = base.copy()
        dr = ImageDraw.Draw(fr)
        # Keep a quiet, contained pulse around the medallion; no long sweep line or travelling dot.
        pulse = int(2 + 3 * (0.5 + 0.5 * math.sin((k / N) * 2 * math.pi)))
        dr.ellipse((88 - 44 - pulse, 91 - 44 - pulse, 88 + 44 + pulse, 91 + 44 + pulse), outline=blend(t["bg1"], accent, 0.6), width=1)
        frames.append(fr)
    return frames'''
        text = text[:achievement_start] + new_loop + text[achievement_end + len("    return frames"):]
    elif "no long sweep line" not in current_loop:
        raise RuntimeError("Achievement animation loop is not the expected original or the known updated version.")

    # Remove both the moving lower progress line/dot and the travelling dot from the Tech Club banner.
    lead_start = text.find("    frames = []", text.find("def leadership_frames"))
    lead_end = text.find("    return frames", lead_start)
    if lead_start < 0 or lead_end < 0:
        raise RuntimeError("Could not locate the Tech Club leadership animation loop.")
    lead_loop = text[lead_start:lead_end + len("    return frames")]
    if "start_x = 46 + int(515 * progress)" in lead_loop:
        new_lead_loop = '''    frames = []
    for k in range(N):
        fr = base.copy()
        dr = ImageDraw.Draw(fr)
        progress = k / max(1, N - 1)
        # A slow pulse remains on the 500+ impact tile; no horizontal sweep or travelling signal.
        r = int(3 + 2 * (0.5 + 0.5 * math.sin(progress * math.pi * 2)))
        dr.ellipse((716 - r, 58 - r, 716 + r, 58 + r), outline=t["teal"], width=1)
        frames.append(fr)
    return frames'''
        text = text[:lead_start] + new_lead_loop + text[lead_end + len("    return frames"):]
    elif "no horizontal sweep" not in lead_loop:
        raise RuntimeError("Leadership animation loop is not the expected original or the known updated version.")

    # New generated loops should already be slow; existing non-generated GIFs are smoothed below.
    text = text.replace("def save_gif(frames: list[Image.Image], path: Path, duration: int = 90, transparent: bool = False)",
                        "def save_gif(frames: list[Image.Image], path: Path, duration: int = 150, transparent: bool = False)")
    for old, new in [
        ("save_gif(achievement_frames(item, theme), path, duration=85)", "save_gif(achievement_frames(item, theme), path, duration=150)"),
        ("save_gif(leadership_frames(theme), lead_path, duration=90)", "save_gif(leadership_frames(theme), lead_path, duration=150)"),
        ("save_gif(heatmap_frames(data, theme), heat_path, duration=80, transparent=True)", "save_gif(heatmap_frames(data, theme), heat_path, duration=150, transparent=True)"),
        ("save_gif(stats_frames(data, theme), stats_path, duration=95)", "save_gif(stats_frames(data, theme), stats_path, duration=150)"),
    ]:
        if old in text:
            text = text.replace(old, new)
        elif new not in text:
            raise RuntimeError(f"Could not find expected output-duration setting: {old}")

    if text != original:
        RENDERER.write_text(text, encoding="utf-8", newline="\n")
        print("Updated scripts/render_profile_motion_assets.py (removed card sweeps; slower loops).")
    else:
        print("Renderer already contains the slower, sweep-free animation loops.")


def patch_portrait_width() -> None:
    # Keep the portrait on the left, but give it 40% of the row instead of 30%.
    patch_text_file(
        UPDATER,
        [
            ('    <td width="30%" align="center" valign="middle">', '    <td width="40%" align="center" valign="middle">'),
            ('    <td width="70%" align="center" valign="middle">', '    <td width="60%" align="center" valign="middle">'),
        ],
        "portrait/stats columns changed to 40% / 60%",
    )


def duration_list(path: Path, image: Image.Image) -> list[int]:
    durations: list[int] = []
    for idx in range(getattr(image, "n_frames", 1)):
        image.seek(idx)
        durations.append(int(image.info.get("duration", 100) or 100))
    return durations


def slower_duration(ms: int) -> int:
    # Idempotent: once a frame duration reaches 150 ms, running this patch again won't keep slowing it.
    if ms >= MIN_DURATION_MS:
        return ms
    return max(MIN_DURATION_MS, int(round((ms * 1.5) / 10.0) * 10))


def slow_gif(path: Path) -> bool:
    """Slow GIF playback by editing Graphic Control Extension delays in the binary.

    The parser skips image-data sub-blocks, so compressed pixels and transparency are
    preserved byte-for-byte; no image decoding/re-encoding is needed for this step.
    """
    data = bytearray(path.read_bytes())
    if not data.startswith((b"GIF87a", b"GIF89a")) or len(data) < 13:
        return False
    changed = False
    pos = 13  # header + logical screen descriptor

    # Skip the global colour table, if one exists.
    packed_screen = data[10]
    if packed_screen & 0x80:
        pos += 3 * (2 ** ((packed_screen & 0x07) + 1))

    length = len(data)
    while pos < length:
        marker = data[pos]
        if marker == 0x3B:  # GIF trailer
            break
        if marker == 0x21:  # Extension block
            if pos + 2 >= length:
                break
            label = data[pos + 1]
            if label == 0xF9:  # Graphic Control Extension
                if pos + 8 > length or data[pos + 2] != 4 or data[pos + 7] != 0:
                    break
                old_cs = data[pos + 4] | (data[pos + 5] << 8)
                if old_cs < 15:  # 15 hundredths = 150 ms
                    new_cs = max(15, int(round(old_cs * 1.5)))
                    data[pos + 4] = new_cs & 0xFF
                    data[pos + 5] = (new_cs >> 8) & 0xFF
                    changed = True
                pos += 8
            else:
                # Other extensions consist of size-prefixed sub-blocks ending in 0.
                pos += 2
                while pos < length:
                    block_size = data[pos]
                    pos += 1
                    if block_size == 0:
                        break
                    pos += block_size
            continue
        if marker == 0x2C:  # Image descriptor
            if pos + 10 > length:
                break
            packed_image = data[pos + 9]
            pos += 10
            if packed_image & 0x80:  # local colour table
                pos += 3 * (2 ** ((packed_image & 0x07) + 1))
            if pos >= length:
                break
            pos += 1  # LZW minimum code size
            # Skip compressed image data sub-blocks; never scan inside them for extension bytes.
            while pos < length:
                block_size = data[pos]
                pos += 1
                if block_size == 0:
                    break
                pos += block_size
            continue
        # Unknown/invalid structure: stop without risking arbitrary edits.
        break

    if changed:
        path.write_bytes(data)
    return changed


def remove_sweep_band(path: Path, top: int, bottom: int, left: int = 0, right: int | None = None) -> bool:
    """Erase the animated underline/wave in a safe empty band, keeping the rest unchanged."""
    if not path.is_file():
        return False
    try:
        with Image.open(path) as im:
            if getattr(im, "n_frames", 1) < 2:
                return False
            original_info = dict(im.info)
            durations = duration_list(path, im)
            frames_rgb: list[Image.Image] = []
            all_bands_already_clean = True
            for idx in range(im.n_frames):
                im.seek(idx)
                frame = im.convert("RGB").copy()
                w, h = frame.size
                band_top = min(max(0, top), h - 2)
                band_bottom = min(max(band_top + 1, bottom), h - 1)
                if band_bottom - band_top < 4:
                    raise RuntimeError(f"Unexpected dimensions for {path.name}: {w}x{h}")
                band_left = min(max(0, left), w - 1)
                band_right = min(w, max(band_left + 1, right if right is not None else w))
                # If every row already matches the clean top scanline, this banner has
                # already been processed; skip it to avoid needless palette re-encoding.
                clean_row = frame.crop((band_left, band_top, band_right, band_top + 1))
                for y in range(band_top + 1, band_bottom):
                    existing_row = frame.crop((band_left, y, band_right, y + 1))
                    if ImageChops.difference(clean_row, existing_row).getbbox():
                        all_bands_already_clean = False
                    frame.paste(clean_row, (band_left, y))
                frames_rgb.append(frame)
            if all_bands_already_clean:
                return False

            # Requantize the opaque banner sequence through one shared palette to keep frames consistent.
            palette = frames_rgb[len(frames_rgb) // 2].quantize(colors=256, method=Image.Quantize.MEDIANCUT)
            pal_frames = [fr.quantize(palette=palette, dither=Image.Dither.NONE) for fr in frames_rgb]
            new_durations = [slower_duration(ms) for ms in durations]
            kwargs = {
                "save_all": True,
                "append_images": pal_frames[1:],
                "duration": new_durations,
                "loop": int(original_info.get("loop", 0)),
                "optimize": True,
                "disposal": 2,
            }
            pal_frames[0].save(path, **kwargs)
            return True
    except Exception as exc:
        raise RuntimeError(f"Could not clean {path.relative_to(ROOT)}: {exc}") from exc



def ensure_subtle_pulse_if_static(path: Path) -> bool:
    """If removing the sweep leaves the leadership card static, add a restrained icon-ring pulse."""
    if not path.is_file():
        return False
    try:
        with Image.open(path) as im:
            if getattr(im, "n_frames", 1) < 2:
                base = im.convert("RGB").copy()
                original_info = dict(im.info)
                durations = [MIN_DURATION_MS] * 16
                needs_pulse = True
                frames = [base]
            else:
                original_info = dict(im.info)
                frames = []
                durations_existing = duration_list(path, im)
                for idx in range(im.n_frames):
                    im.seek(idx)
                    frames.append(im.convert("RGB").copy())
                # A pulse is needed only if all frames are effectively identical after removing the sweep.
                base = frames[0]
                needs_pulse = not any(ImageChops.difference(base, fr).getbbox() for fr in frames[1:])
                durations = durations_existing
            if not needs_pulse:
                return False

            w, h = base.size
            if w < 500 or h < 180:
                return False
            # The original banner's circular icon sits at about (90, 115) in the 1100 x 230 card.
            cx, cy = int(w * 0.082), int(h * 0.50)
            pulse_frames: list[Image.Image] = []
            for idx in range(16):
                phase = idx / 16.0
                radius = 38 + int(round(4 * (0.5 - 0.5 * math.cos(2 * math.pi * phase))))
                fr = base.copy()
                dr = ImageDraw.Draw(fr)
                dr.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), outline=(46, 100, 157), width=1)
                pulse_frames.append(fr)

            palette = pulse_frames[len(pulse_frames) // 2].quantize(colors=256, method=Image.Quantize.MEDIANCUT)
            pal_frames = [fr.quantize(palette=palette, dither=Image.Dither.NONE) for fr in pulse_frames]
            pal_frames[0].save(
                path,
                save_all=True,
                append_images=pal_frames[1:],
                duration=[180] * len(pal_frames),
                loop=int(original_info.get("loop", 0)),
                optimize=True,
                disposal=2,
            )
            return True
    except Exception as exc:
        raise RuntimeError(f"Could not preserve motion on {path.relative_to(ROOT)}: {exc}") from exc

def local_readme_refs() -> tuple[int, list[str]]:
    text = README.read_text(encoding="utf-8")
    refs: set[str] = set()
    for match in re.finditer(r'\b(?:src|srcset)\s*=\s*["\']([^"\']+)["\']', text, re.I):
        for candidate in match.group(1).split(","):
            candidate = candidate.strip()
            if not candidate:
                continue
            uri = candidate.split()[0].split("?", 1)[0].split("#", 1)[0]
            if uri.startswith("./"):
                refs.add(uri[2:])
    missing = sorted(item for item in refs if not (ROOT / item).is_file())
    return len(refs), missing


def main() -> int:
    if not README.is_file():
        print("ERROR: Run this script from the repository root; README.md was not found.")
        return 2
    git_dir = ROOT / ".git"
    if git_dir.is_dir() and ((git_dir / "rebase-merge").exists() or (git_dir / "rebase-apply").exists()):
        print("ERROR: A Git rebase is still in progress. Finish the rebase before applying this patch.")
        print("Run: git status")
        return 3
    required = [UPDATER, RENDERER, ROOT / "data" / "contributions.json"]
    missing = [p.relative_to(ROOT).as_posix() for p in required if not p.is_file()]
    if missing:
        print("ERROR: Required files are missing: " + ", ".join(missing))
        print("Apply the Profile Motion Upgrade patch first, then run this patch from the repo root.")
        return 4

    try:
        patch_renderer()
        patch_portrait_width()
    except Exception as exc:
        print(f"ERROR while preparing the animation source: {exc}")
        return 5

    print("Regenerating theme-aware motion assets and refreshing the README image blocks...")
    result = subprocess.run([sys.executable, str(UPDATER)], cwd=ROOT)
    if result.returncode:
        print("ERROR: Existing motion updater failed. Review its output; no push was attempted.")
        return result.returncode

    # Calm all looping visuals under assets/animated and the top-level profile banner GIFs.
    gif_paths = sorted(ANIM.rglob("*.gif"))
    gif_paths.extend(p for p in (ROOT / "banner-dark.gif", ROOT / "banner-light.gif") if p.is_file())
    slowed = 0
    for path in gif_paths:
        if slow_gif(path):
            slowed += 1
    print(f"Slowed {slowed} GIFs to a calmer pace (minimum frame delay: {MIN_DURATION_MS} ms).")

    # The two project cards contain a travelling underline and wave in the empty bottom band.
    # The older AI Build Challenge leadership card has a scanline and wave in its lower band.
    cleaned = 0
    for name in (
        "project-urjanetra-dark.gif", "project-urjanetra-light.gif",
        "project-ayuscout-dark.gif", "project-ayuscout-light.gif",
    ):
        if remove_sweep_band(ANIM / name, top=171, bottom=224):
            cleaned += 1
            print(f"Removed travelling underline/wave: assets/animated/{name}")
    for name in ("leadership-ai-build-challenge-dark.gif", "leadership-ai-build-challenge-light.gif"):
        path = ANIM / name
        if path.is_file():
            with Image.open(path) as probe:
                is_wide_card = probe.height <= 250
            # In the wide 1100 x 230 card, the sweep is confined to the bottom 10 pixels.
            # Keep the icon and title untouched; only remove the travelling underline/track.
            top, bottom = (216, 226) if is_wide_card else (194, 273)
            did_clean = remove_sweep_band(path, top=top, bottom=bottom)
            added_pulse = ensure_subtle_pulse_if_static(path) if is_wide_card else False
            if did_clean or added_pulse:
                cleaned += 1
                detail = "removed sweep and preserved a subtle icon pulse" if added_pulse else "removed scanline/wave"
                print(f"Updated leadership banner ({detail}): assets/animated/{name}")
    print(f"Cleaned {cleaned} existing project/leadership banners.")

    count, missing_refs = local_readme_refs()
    if missing_refs:
        print("ERROR: Local README assets are missing after the update:")
        for name in missing_refs:
            print(" -", name)
        return 6
    print(f"README local image references: {count}; missing: 0.")
    print("Complete. Review the result with:")
    print("  git diff --check")
    print("  python .\\scripts\\validate_profile_assets.py")
    print("  git diff -- README.md scripts\\render_profile_motion_assets.py apply_profile_motion_refinement.py")
    print("Then inspect git status --short before staging anything.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
