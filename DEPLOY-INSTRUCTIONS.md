# Selective rollback deployment — Archit Anshuman

This pack restores the section layout/accent headers from the supplied reference README while preserving Archit's custom animated banner (`banner-dark.gif` / `banner-light.gif`) and real-photo ASCII portrait (`assets/animated/profile-photo-ascii-dark.gif` / light). It retains the resume-specific project, achievement, skills, stats and contribution graphics. The source photos are not included.

## Critical: recover Git safely first

Open PowerShell in `C:\Users\archi\Documents\profile-readme-build`. If Git reports a rebase in progress, run `git rebase --abort` first. Then check `git status`. Do not use `git push --force`.

Create a backup branch after the rebase is aborted:

```powershell
git branch "backup-before-selective-rollback-$(Get-Date -Format yyyyMMdd-HHmmss)"
git fetch origin
```

If `git status` has no tracked local modifications, base local `main` on the current remote to avoid another divergence/rebase conflict:

```powershell
git switch main
git reset --hard origin/main
```

The backup branch keeps the local profile commit you are rolling back. Do not run the reset if Git reports tracked modifications that you still need to preserve; stop and inspect them first.

## Copy files

Extract this ZIP to a temporary folder. Copy its contents into `C:\Users\archi\Documents\profile-readme-build`, allowing the README and matching assets/scripts/workflows to be replaced. Do not delete `.git`, `.venv`, or `data/contributions.json`. The package intentionally omits `data/contributions.json` so the latest repository snapshot stays in place.

## Regenerate and validate

```powershell
cd "$HOME\Documents\profile-readme-build"
.\.venv\Scripts\Activate.ps1
python -m pip install -r scripts/requirements.txt
python scripts/update_contribution_visuals.py
python scripts/validate_profile_assets.py
```

The generator uses the existing `data/contributions.json`, ensuring the annual heatmap, activity graph, overview and stats card are regenerated together. To fetch a new snapshot first, run `python scripts/fetch_contributions.py` and then `python scripts/update_contribution_visuals.py`; this step needs internet access.

## Review and push

```powershell
git rm --cached --ignore-unmatch yes1.jpg "yes1(2).jpg" pic.png source-photo.png source-prepped.png
git add -A
git diff --cached --check
git diff --cached --name-only
```

Inspect the staged file list. Ensure no original photo has been staged. Then commit and push:

```powershell
git commit -m "Restore reference-style layout and preserve Archit banner portrait"
git push origin main
```

Because the branch was reset to the latest `origin/main` before merging these files, the push should be a normal fast-forward unless another workflow commits in the meantime. If a push is rejected, run `git fetch origin` and stop before pulling; inspect the changed commits first.

## After publishing

Open GitHub Actions and manually run `Update profile art`, then `Generate Snake Animation`. Refresh the profile with Ctrl+F5. Section header SVGs use light/dark theme pairs; the banner and real-photo ASCII portrait retain their looping GIF animations.
