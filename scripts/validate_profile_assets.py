#!/usr/bin/env python3
"""Validate SVG XML and every local image source referenced by the profile README."""
from pathlib import Path
import re, sys, xml.etree.ElementTree as ET
ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
text = README.read_text(encoding="utf-8")
missing=[]
for attr in ("src", "srcset"):
    for value in re.findall(rf'{attr}="([^"]+)"', text):
        for item in value.split(","):
            url=item.strip().split()[0]
            if url.startswith("./"):
                path=url[2:].split("?")[0].split("#")[0]
                if not (ROOT/path).is_file(): missing.append(path)
svgs=[p for p in ROOT.rglob("*.svg") if ".git" not in p.parts and ".venv" not in p.parts]
errors=[]
for p in svgs:
    try: ET.parse(p)
    except ET.ParseError as e: errors.append(f"{p.relative_to(ROOT)}: {e}")
ref_matches = re.findall(r'(?:src|srcset)="([^"]+)"', text)
print(f"README local image refs checked: {len(set(ref_matches))} raw attributes")
print(f"SVG files validated: {len(svgs)}")
if missing:
    print("Missing local assets:")
    for p in sorted(set(missing)): print(f"  - {p}")
if errors:
    print("Invalid SVG files:")
    for e in errors: print(f"  - {e}")
if missing or errors: sys.exit(1)
print("Profile asset validation passed.")
