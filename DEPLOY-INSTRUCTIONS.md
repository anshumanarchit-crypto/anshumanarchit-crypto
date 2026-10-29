# Deploy the Archit Anshuman Animated Profile Kit

This ZIP is an **overlay for the existing** `anshumanarchit-crypto/anshumanarchit-crypto` profile repository. It is not a separate project to publish under a different repository name.

## Design

- Theme-aware banner with animated cobalt/teal signal lines and resume-matched title.
- A custom ASCII SVG made from the supplied laptop-character illustration. The original PNG is deliberately **not** included, so the public repo need not expose the source image.
- Theme-aware activity, stats, project, skills, leadership and achievement visuals.
- The leadership graphic is **AI Build Challenge — Bengaluru 2026, 1st Runner-Up, Team Lead**; AyuScout is used only as a project.
- LinkedIn, email and HackerRank links use Archit Anshuman's supplied URLs.
- The SVG generator uses Python's standard library and XML-validates every file it writes.

## Apply it on Windows PowerShell

1. Download and extract this ZIP.
2. Copy/merge the ZIP's contents into `C:\Users\archi\Documents\profile-readme-build`. Allow `README.md`, `.gitignore`, `scripts/requirements.txt` and `.github/workflows/update-profile-art.yml` to be replaced. Copy the new `assets` folder and `scripts/generate_profile_assets.py`. Keep the existing `data/contributions.json` and `scripts/fetch_contributions.py`.
3. Open PowerShell in the project directory and activate your venv:

   ```powershell
   cd "$HOME\Documents\profile-readme-build"
   .\.venv\Scripts\Activate.ps1
   $env:GH_PROFILE_USER = "anshumanarchit-crypto"
   python -m pip install -r scripts/requirements.txt
   python scripts/fetch_contributions.py
   python scripts/generate_profile_assets.py
   ```

4. Confirm these files exist and open without XML parse errors:

   ```powershell
   Test-Path .\profile-ascii.svg
   Test-Path .\profile-ascii-light.svg
   Test-Path .\stats.svg
   Test-Path .\stats-light.svg
   Test-Path .\contrib-heatmap.svg
   Test-Path .\contrib-heatmap-light.svg
   python -c "import xml.etree.ElementTree as ET; from pathlib import Path; files=[p for p in Path('.').rglob('*.svg') if p.name not in {'info-card.svg','ascii-portrait.svg'}]; [ET.parse(p) for p in files]; print(f'Validated {len(files)} SVG files')"
   ```

5. Review `.gitignore`; don't commit your source character PNG or any private photos. The SVG portrait is already included.
6. Remove already tracked original photos from the Git index if you don't want them public:

   ```powershell
   git rm --cached --ignore-unmatch yes1.jpg source-prepped.png source-photo.png pic.png info-card.svg ascii-portrait.svg
   Remove-Item .\info-card.svg, .\ascii-portrait.svg -ErrorAction SilentlyContinue
   ```

   This removes the superseded broken info card from the working folder and removes those files from the next repository version. The `git rm --cached` operation alone does not remove local files. It does not erase copies from earlier Git history.
7. Review and push:

   ```powershell
   git add .
   git status
   git commit -m "Refresh Archit Anshuman animated profile"
   git push
   ```

8. On GitHub open **Actions**. Run **Refresh profile visuals** and **Generate contribution snake** manually once. Both workflows need repository `contents: write` permission. The contribution-snake images are published to the `output` branch; they may be unavailable until that first workflow succeeds.
9. Hard-refresh the profile page with `Ctrl+F5`.

## Notes

- The repository username in terminal chrome is `anshumanarchit-crypto`; the display name is `Archit Anshuman`.
- The monthly graph and contribution heatmaps are generated from `data/contributions.json`, not fabricated profile statistics.
- The skills/project/achievement cards are designed for both GitHub light and dark themes using `<picture>` source selection.
- The README includes the resume's own reported AyuScout metrics with clear attribution as resume-reported estimates.
