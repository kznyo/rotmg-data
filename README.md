# RotMG Data

Keeps the game data of the RotMG apps up to date. One scheduled workflow watches Deca's launcher for a new Realm of the Mad God Exalt build and, when one appears, runs each app's own extractor on it and commits the result to that app's repo.

Apps:
- [rotmg-sprite-index](https://github.com/kznyo/rotmg-sprite-index)
- [rotmg-dps-calculator](https://github.com/kznyo/rotmg-dps-calculator)

This repo never contains game files, only the download script and the workflow.

## Downloading a build
`download.py` needs only the Python standard library.
```sh
python download.py --version    # print the current build version
python download.py <builds>     # download it into <builds>/<build version>/
```
It downloads `globalgamemanagers*` and `resources.assets*` (about 540 MB unpacked), which hold the game XML, the sprite index and the sprite atlases, checks each file against Deca's checksums and writes `build.json` with the launcher's build info. Keep `<builds>` outside any repo.

## The workflow
`.github/workflows/update.yml` runs hourly and by hand from the Actions tab:
1. `check` compares the launcher's build version with `build.json` and stops within seconds if they match.
2. `extract` runs once per app, side by side. It skips an app whose data already has the build; otherwise it downloads the build, runs the app's extractor tests and `extract.py`, and commits `data/` to the app's default branch. The app's host deploys from that push.
3. `record` writes the new version to `build.json`, only when every app succeeded. A failed app is retried on the next run, and the apps that already have the build are skipped.

These commits also keep the schedule alive: GitHub disables scheduled workflows in public repos after 60 days without activity.

### Setup
Create a fine-grained personal access token with **Contents: Read and write** on the app repos and save it as the Actions secret `APPS_TOKEN`.

### Adding an app
Add its repo to the `extract` matrix. The workflow expects the app to have:
- `extractor/requirements.txt` and tests that `python -m pytest extractor` runs
- `python extractor/extract.py <build folder> data`, writing its data into `data/`
- a file in `data/` with a top-level `"build"` (the build version), named as the matrix's `build-file`

If the app needs other game files than the ones above, widen `WANTED` in `download.py`.
