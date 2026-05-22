# Installation Guide - Clipmanx

Clipmanx is a lightweight clipboard manager for Linux Mint 22.3+ with GTK3 system tray integration.

## Quick Install (Recommended)

For **Linux Mint 22.3+, Ubuntu, and Debian-based systems**:

```bash
curl -sSL https://raw.githubusercontent.com/vicsejas/clipmanx/main/install-latest.sh | sudo bash
```

Or manually download and run:

```bash
sudo bash install-latest.sh
```

## Manual Installation

### Option 1: Install from Pre-built .deb (Easiest)

1. Download the latest `.deb` file from [GitHub Releases](https://github.com/vicsejas/clipmanx/releases)
2. Install it:
   ```bash
   sudo apt-get install -y ./clipmanx_0.1.0-1_all.deb
   ```

### Option 2: Build from Source

Requirements:
- `python3.10+`
- `python3-gi`
- `gir1.2-gtk-3.0`
- `debhelper-compat`
- `python3-setuptools`
- `pybuild-plugin-pyproject`

Steps:
```bash
# Clone the repository
git clone https://github.com/vicsejas/clipmanx.git
cd clipmanx

# Install build dependencies
sudo apt-get install debhelper-compat python3-setuptools python3-all pybuild-plugin-pyproject python3-gi gir1.2-gtk-3.0

# Build the .deb package
dpkg-buildpackage -us -uc -b

# Install the built package (with dependency handling)
cd ..
sudo apt-get install -y ./clipmanx_*.deb
```

For detailed build instructions, see [BUILD_GUIDE.md](BUILD_GUIDE.md).

## System Requirements

- **OS**: Linux Mint 22.3+ (or any Debian/Ubuntu-based system)
- **Python**: 3.10 or later
- **GTK**: 3.0
- **Dependencies**: 
  - `python3-gi`
  - `gir1.2-gtk-3.0`

## First Launch

After installation, you can launch Clipmanx by:

- **Terminal**: `clipmanx`
- **Applications Menu**: Search for "Clipmanx"
- **System Tray**: The app appears in the system tray once started

## Configuration

Settings are stored in `~/.config/clipmanx/settings.json`

Available settings:
- `capture_clipboard`: Capture Ctrl+C clipboard events (default: true)
- `capture_primary`: Capture PRIMARY selection (xselection) (default: true)
- `max_items`: Maximum history items to store (default: 50)

## Uninstall

```bash
sudo apt-get remove clipmanx
```

To also remove configuration files:
```bash
sudo apt-get remove --purge clipmanx
rm -rf ~/.config/clipmanx
```

## Troubleshooting

### Icon not showing in system tray
- Ensure your system has a tray-capable panel (MATE Panel works well on Linux Mint)
- Try restarting the application: `killall clipmanx && clipmanx`

### Clipboard not capturing
- Ensure both "Capture system clipboard" and "Capture selection" are enabled in settings
- Check that your clipboard manager isn't conflicting (e.g., with `xclip`)

### Dependencies missing error
Run: `sudo apt-get install python3-gi gir1.2-gtk-3.0`

## Building Releases

### For Maintainers

Create a new release with automatic .deb building:

1. Update version in `pyproject.toml`
2. Commit changes
3. Create a git tag:
   ```bash
   git tag -a v0.1.0 -m "Release version 0.1.0"
   git push origin v0.1.0
   ```
4. GitHub Actions automatically builds and uploads the `.deb` to releases

## Support

- **Issues**: https://github.com/vicsejas/clipmanx/issues
- **Discussions**: https://github.com/vicsejas/clipmanx/discussions

---

**Last Updated**: May 2026
**Supported**: Linux Mint 22.3+
