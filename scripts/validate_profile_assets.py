#!/usr/bin/env python3
"""Validate README local image paths, SVG XML, and forbidden old identity strings."""
from pathlib import Path
import re, sys, xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
readme=(ROOT/'README.md').read_text(encoding='utf-8')
refs=re.findall(r'(?:src|srcset)="([^"]+)"', readme)
local=[]
for ref in refs:
    for item in ref.split(','):
        parts=item.strip().split()
        if not parts: continue
        u=parts[0]
        if u.startswith('./'): local.append(u[2:].split('?')[0].split('#')[0])
missing=sorted({p for p in local if not (ROOT/p).is_file()})
svgs=list(ROOT.rglob('*.svg'))
for p in svgs: ET.parse(p)
text_files=[p for p in ROOT.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name != 'validate_profile_assets.py' and p.suffix.lower() in {'.md','.txt','.py','.yml','.yaml','.json'}]
forbidden=('Arpit'+'248-3','Arpit'+' Jham','Lee'+'tCode')
hits=[]
for p in text_files:
    text=p.read_text(encoding='utf-8',errors='ignore')
    for term in forbidden:
        if term.casefold() in text.casefold(): hits.append((p.relative_to(ROOT).as_posix(),term))
print(f'README local image attributes checked: {len(refs)}')
print(f'Unique local image targets checked: {len(set(local))}')
print(f'SVG XML files validated: {len(svgs)}')
if missing: print('Missing local images:\n'+'\n'.join(missing))
if hits: print('Old profile references found:\n'+'\n'.join(f'{p}: {t}' for p,t in hits))
if missing or hits: sys.exit(1)
print('Profile asset validation passed.')
