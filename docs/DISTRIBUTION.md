# Distribution & Release Guide

This document explains how Clipmanx is released via GitHub Releases.

## Overview

Clipmanx uses a **GitHub Actions + GitHub Releases** workflow:

1. You push a git tag matching `v*` (e.g. `v0.1.2`)
2. GitHub Actions builds the `.deb` package via `dpkg-buildpackage`
3. The `.deb` is uploaded as an asset on the GitHub Release for that tag
4. Users download the `.deb` from the Releases page and install it with apt

## Prerequisites

- The repo is pushed to GitHub
- GitHub Actions is enabled (default for public repos)
- The workflow has `permissions: contents: write` so it can create releases

## Release Checklist

### 1. Prepare Release

```bash
# Update version in pyproject.toml
$EDITOR pyproject.toml
# e.g. version = "0.1.2" → version = "0.1.3"

# Prepend a new entry to debian/changelog (the format is strict — two spaces
# before each '*', single space then '--' before the maintainer line,
# RFC 5322 date from `date -R`)
$EDITOR debian/changelog

# Sync uv.lock to the new version
uv lock

# Commit the release bump
git add pyproject.toml debian/changelog uv.lock
git commit -m "Release v0.1.3"
```

### 2. Tag and Push

```bash
git tag v0.1.3
git push origin main
git push origin v0.1.3
```

### 3. Watch the Workflow

- Open https://github.com/vicsejas/clipmanx/actions
- The "Build .deb Package" run for the new tag should succeed
- The `.deb` is automatically attached to the release

### 4. Verify Release

- Open https://github.com/vicsejas/clipmanx/releases
- Confirm `clipmanx_0.1.3_all.deb` is attached
- Edit the release notes from the auto-generated draft if desired

## Install Path for Users

Users grab the `.deb` from the Releases page and install with apt
(which resolves the GTK runtime dependencies for them):

```bash
sudo apt-get install -y ./clipmanx_*_all.deb
```

This is the **only** supported install path. The legacy `install-latest.sh`
one-liner is no longer documented.

## Debian Package Contents

```
/usr/bin/clipmanx                          → executable entry point
/usr/lib/python3/dist-packages/clipmanx/   → Python package
/usr/share/applications/clipmanx.desktop   → desktop entry
/usr/share/pixmaps/clipmanx.png            → app icon
```

System-wide install; per-user config lives at `~/.config/clipmanx/settings.json`.

## Workflow File

The release workflow lives at [`.github/workflows/build-deb.yml`](../.github/workflows/build-deb.yml).
Key knobs:

```yaml
on:
  push:
    tags: ['v*']

permissions:
  contents: write          # required to create the GitHub release

jobs:
  build:
    runs-on: ubuntu-24.04  # closest match to Linux Mint 22.x
```

## Re-tagging After a Workflow Fix

If the workflow fails (broken pinned action SHA, missing apt dependency,
etc.) and the fix is on `main` but the tag still points to the broken
commit, force-move the tag — releases that have never produced an asset are
safe to overwrite:

```bash
git tag -f v0.1.3
git push -f origin v0.1.3
```

## Post-Release

1. Announce on relevant channels
2. Update docs if behavior changed
3. Monitor issues for user feedback

## Troubleshooting Builds

Check the workflow logs at https://github.com/vicsejas/clipmanx/actions.
Recurring causes:

- Missing `Build-Depends` in `debian/control`
- Pinned third-party action SHA that doesn't resolve (use a real SHA or a
  `@v2`-style tag)
- Missing `permissions: contents: write` (causes 403 on release upload)

## Alternative Distribution Methods (Future)

Out of scope today but worth knowing about:

- **APT repository** — host your own Debian repo (needs hosting + GPG signing)
- **Ubuntu Universe** — go through Debian/Ubuntu maintainer sponsorship
- **AppImage** — distribution-agnostic single-file bundle
- **Snap / Flatpak** — universal Linux packages

For now, GitHub Releases serving `.deb`s is the simplest model.
