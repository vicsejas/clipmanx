# Distribution & Release Guide

This document explains how to distribute Clipmanx via GitHub Releases.

## Overview

Clipmanx uses a **GitHub Actions + GitHub Releases** workflow:

1. **You push a git tag** (e.g., `v0.1.0`)
2. **GitHub Actions automatically builds** the `.deb` package
3. **The `.deb` is uploaded** to GitHub Releases
4. **Users download and install** via the installer script or manual download

## Prerequisites

1. GitHub repository initialized (`git remote add origin ...`)
2. Repository pushed to GitHub
3. GitHub Actions enabled (default for public repos)

## Release Checklist

### 1. Prepare Release

```bash
# Update version in pyproject.toml
nano pyproject.toml
# Change: version = "0.1.0" → version = "0.2.0"

# Update debian/changelog
nano debian/changelog
# Add new entry at top with current date

# Commit
git add pyproject.toml debian/changelog
git commit -m "Bump version to 0.2.0"
```

### 2. Create Release Tag

```bash
git tag -a v0.2.0 -m "Release version 0.2.0"
git push origin main
git push origin v0.2.0
```

### 3. Wait for GitHub Actions

- Go to: https://github.com/vicsejas/clipmanx/actions
- Watch the "Build .deb Package" workflow complete
- The `.deb` file will be automatically attached to the release

### 4. Verify Release

- Visit: https://github.com/vicsejas/clipmanx/releases
- Check that `.deb` file is attached
- Edit release notes if needed

## File Structure for Distribution

When users download from GitHub Releases, they get:

```
clipmanx_0.2.0-1_all.deb  ← Pre-built package
```

Users can then either:
1. **One-line install** (downloads `.deb` from release):
   ```bash
   curl -sSL https://raw.githubusercontent.com/vicsejas/clipmanx/main/install-latest.sh | sudo bash
   ```

2. **Manual install**:
   - Download `.deb` from releases page
   - Run: `sudo apt-get install -y ./clipmanx_*.deb`

## Debian Package Contents

The built `.deb` includes:

```
/usr/bin/clipmanx                                  → Executable
/usr/lib/python3/dist-packages/clipmanx/          → Python package
/usr/share/applications/clipmanx.desktop          → Desktop entry
/usr/share/pixmaps/clipmanx.png                   → App logo
```

## System-Wide Installation

The `.deb` package is installed system-wide:

- **Binary location**: `/usr/bin/clipmanx` (available to all users)
- **Config location**: `~/.config/clipmanx/settings.json` (per-user)
- **Autostart**: Desktop entry in `/usr/share/applications/`

All users on the system can access the app after installation.

## Updating GitHub Actions Workflow

To change build settings, edit `.github/workflows/build-deb.yml`:

```yaml
# Triggered on any tag push starting with 'v'
on:
  push:
    tags:
      - 'v*'

# Builds on Ubuntu 24.04 (closest to Linux Mint)
runs-on: ubuntu-24.04

# Auto-uploads .deb to GitHub Releases
```

## Development Workflow

When developing locally:
```bash
uv sync          # Install dependencies
uv run clipmanx   # Run the app
```

## Post-Release

After a successful release:

1. **Announce** on any channels (Reddit, forums, etc.)
2. **Update docs** if behavior changed
3. **Monitor issues** for user feedback
4. **Plan next release** based on feedback

## Troubleshooting Builds

### Build failed in GitHub Actions
- Check workflow logs: https://github.com/vicsejas/clipmanx/actions
- Common issues:
  - Missing dependencies in `Build-Depends` (debian/control)
  - Syntax errors in debian/rules
  - File paths incorrect

### Fix and retry
```bash
# Fix the issue in debian/ files
git add debian/
git commit -m "Fix build config"

# Delete old tag
git tag -d v0.2.0
git push origin :refs/tags/v0.2.0

# Re-tag and push
git tag -a v0.2.0 -m "Release version 0.2.0"
git push origin v0.2.0
```

## Alternative Distribution Methods

### 1. Create APT Repository (Advanced)
Host your own Debian repository so users can:
```bash
apt-get install clipmanx
```
Requires: server hosting, GPG signing, repo management

### 2. Publish to Ubuntu Universe
Get into official Ubuntu/Debian repositories. Requires:
- Package sponsorship
- Compliance with Debian policy
- Ongoing maintenance

### 3. AppImage (More Portable)
Works on any Linux distro, not Debian-specific. Requires PyAppImage tools.

### 4. Snap Package
Universal Linux package. `snap install clipmanx`

---

For now, **GitHub Releases** is the easiest approach and gives users a simple one-line install.
