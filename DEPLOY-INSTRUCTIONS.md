# Archit Anshuman Animated Profile — Apply and Validate

This package is based on the uploaded reference profile's terminal-card layout and looping GIF approach, with Archit's resume content. It includes no `.git` directory and does not include the original source photos.

## Important architecture
- `banner-dark.gif` / `banner-light.gif`: looping terminal banner. The left ASCII art is derived from the supplied cartoon laptop character; the right panel cycles `WELCOME` then `I'M ARCHIT ANSHUMAN` and uses `anshumanarchit-crypto` in the prompt pill.
- `assets/animated/profile-photo-ascii-*.gif`: looping top-to-bottom ASCII portrait derived from Archit's real photo. Only the generated GIFs are included; the source JPG stays private.
- All contribution-dependent GIFs (`developer-overview`, `activity-graph`, `annual-heatmap`, `contribution-stats`, `contribution-snake`) are generated from the same `data/contributions.json`, so the counts agree with each other.
- Section headers are actual looping dark/light GIFs, not unanimated SVG badges.
- The Achievements section is graphics-only and includes AI for Bharat, AI Build Challenge, Global Academy finalist, HackerRank Orchestrate Rank 418, and the HackerRank 5-Star MySQL badge.

## Apply on Windows
1. Extract this ZIP to a temporary folder.
2. Merge the extracted contents into `C:\Users\archi\Documents\profile-readme-build`, overwriting matching profile files. Keep the existing `.git` folder and `.venv` folder. The ZIP does not contain original source images.
3. Open PowerShell at the project root and run:
   ```powershell
   cd "$HOME\Documents\profile-readme-build"
   .\.venv\Scripts\Activate.ps1
   python -m pip install -r scripts/requirements.txt
   $env:GH_PROFILE_USER = "anshumanarchit-crypto"
   python scripts/fetch_contributions.py
   python scripts/update_contribution_visuals.py
   python scripts/validate_profile_assets.py
   ```
   The fetch and renderer scripts update all contribution charts from one JSON snapshot, so heatmap/stats totals agree. Do not stage source images such as `yes1.jpg`, `yes1(2).jpg`, `pic.png`, `source-photo.png` or `source-prepped.png`.
4. Review, commit, synchronize, and push:
   ```powershell
   git status
   git add -A
   git diff --cached --check
   git diff --cached --stat
   git commit -m "Refine Archit Anshuman animated profile"
   git fetch origin
   git pull --rebase origin main
   git push
   ```
   If `pull --rebase` reports a conflict, stop and resolve it deliberately. Never use `git push --force`.
5. Open the repository's **Actions** tab. Run **Update profile art** manually once. It also runs daily. This workflow commits contribution GIFs back to `main`, so it intentionally does not trigger on every main push; after a manual workflow run makes a remote commit, run `git fetch origin` / `git pull --rebase origin main` before your next local push.

## Regenerate the personal portrait/banners locally
The package includes generated GIFs and does not include your source photo or cartoon PNG. If you later want to regenerate those GIFs, run this locally (adjust the paths if you moved the files):
```powershell
python scripts/generate_profile_assets.py --photo "$HOME\OneDrive\Desktop\yes1.jpg" --banner-art "$HOME\Downloads\pic.png"
python scripts/validate_profile_assets.py
```
The script reads the source images locally and writes only the derived GIFs into the repository; it does not copy the source images into the ZIP or repository. Do not run this generator in GitHub Actions.

## Update contributions later
GitHub Actions uses `GH_PROFILE_USER=anshumanarchit-crypto`, fetches one public contribution snapshot, and regenerates the developer overview, activity line, annual heatmap, stats card and contribution snake from that same JSON. It does not regenerate your personal portrait/banner, because source photos are intentionally private.

## Note about public/private contributions
The included contribution JSON is a public-calendar snapshot as of 2026-10-29. If GitHub has changed counts since then, run the workflow to fetch a fresh snapshot; all cards are regenerated together to keep their totals synchronized.
