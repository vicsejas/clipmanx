# Installation

Clipmanx is distributed as a Debian package built by CI on every `v*` tag.

## Install

1. Download the latest `clipmanx_*_all.deb` from the
   [Releases page](https://github.com/vicsejas/clipmanx/releases).
2. Install it (apt resolves the GTK runtime dependencies for you):

   ```bash
   sudo apt-get install -y ./clipmanx_*_all.deb
   ```

## System Requirements

- **OS**: Linux Mint 22.3+ (or any Debian/Ubuntu-based system with GTK 3)
- **Python**: 3.10+ (pulled in by the package as `python3-gi` + `gir1.2-gtk-3.0`)

## First Launch

After installation, launch Clipmanx by:

- **Terminal**: `clipmanx`
- **Applications Menu**: search for "Clipmanx"
- **System Tray**: the icon appears once started

## Configuration

Settings are stored at `~/.config/clipmanx/settings.json`. Editable via the
Settings UI (click the tray icon → **Settings**). Available keys:

- `capture_clipboard` — capture Ctrl+C events (default: `true`)
- `capture_primary` — capture PRIMARY selection / xselect (default: `false`)
- `ignore_terminals` — drop copies whose source window is a terminal (default: `true`)
- `max_items` — maximum history entries (default: `50`)
- `icon_theme` — `auto`, `light`, `dark` (default: `auto`)
- `tooltip_delay` — milliseconds before tooltips appear (default: `500`)

## Uninstall

```bash
sudo apt-get remove clipmanx        # keep config
sudo apt-get purge clipmanx         # also remove config
rm -rf ~/.config/clipmanx           # also remove per-user settings
```

## Troubleshooting

**Icon not showing in system tray**
Ensure your panel supports a status-icon tray (MATE Panel / Cinnamon panel
work). Restart the app: `pkill -f bin/clipmanx && clipmanx`.

**Nothing happens on tray click**
A stale background instance from a previous run may be holding the
single-instance socket. Kill it and relaunch:

```bash
pkill -f bin/clipmanx
rm -f "${XDG_RUNTIME_DIR:-/tmp}"/clipmanx.sock
clipmanx
```

**Run in foreground to see logs**

```bash
clipmanx --debug
```

Debug output is written to `log.txt` next to the project root, and faults are
captured in `crash.log`.

## Support

- Issues: https://github.com/vicsejas/clipmanx/issues
