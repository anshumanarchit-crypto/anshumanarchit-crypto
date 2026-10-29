#!/usr/bin/env python3
import json
from pathlib import Path
from profile_contribution_renderer import gen_contribution_assets_from_file
ROOT=Path(__file__).resolve().parents[1]
data=json.loads((ROOT/"data"/"contributions.json").read_text(encoding="utf-8"))
gen_contribution_assets_from_file(ROOT,data)
print(f"Refreshed contribution GIFs from {data['total_contributions']} contributions / {data['active_days']} active days.")
