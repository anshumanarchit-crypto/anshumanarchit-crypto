# Apply this profile render fix

The visible broken images came from missing `assets/` files on GitHub. The README references those files, but they were not all present in the remote `main` branch. This bundle includes the complete `assets/` directory and updated README/banner/tagline animations.

## Copy/merge
1. Extract this ZIP.
2. Copy its contents into `C:\Users\archi\Documents\profile-readme-build`. Choose **merge folders** and overwrite matching files.
3. Do not delete `.git`, `data/contributions.json`, or your local venv. No private original photo is included.

## Validate
From PowerShell at the project root:

```powershell
python scripts/validate_profile_assets.py
```

It should report all local README image paths found and every SVG valid.

## Stage the missing assets (important)

```powershell
git status
git add -A README.md banner-dark.gif banner-light.gif assets scripts/validate_profile_assets.py APPLY-THIS-FIX.md
git diff --cached --stat
```

Review the staged files. Make sure `yes1.jpg`, `pic.png`, `source-photo.png`, and `source-prepped.png` are not staged. This package embeds the mascot in the GIF and does not include the source picture.

Then commit and push:

```powershell
git commit -m "Fix profile assets and restore section animations"
git push
```

If the push is rejected because GitHub advanced `main`, run `git fetch origin`, then `git pull --rebase origin main`. Resolve any conflicts carefully; do not force-push.

## After push
Open GitHub Actions and run `Update profile art` and `Generate Snake Animation` once. The README now uses six looping, theme-aware section headers: About, Contributions, Leadership Experience, Technical Skills, Featured Projects, Achievements. Education is included in About instead of creating an extra seventh numbered section.
