# Clipmanx

A lightweight clipboard manager for Linux Mint with GTK3 system tray integration.

![Logo](src/clipmanx/assets/logo.png)

## Features

- **Clipboard History**: Stores and manages clipboard history
- **System Tray Icon**: Adaptive icon (dark/light theme support)
- **Lightweight**: Minimal dependencies, minimal resource usage
- **Persistent**: Remembers clipboard history between sessions
- **Configurable**: Customize capture sources and history size
- **Linux Mint Native**: System-wide installation on Debian-based systems

## Installation

### Quick Install (One-liner)

```bash
curl -sSL https://raw.githubusercontent.com/vicsejas/clipmanx/main/install-latest.sh | sudo bash
```

### Manual Install

See [Installation Guide](docs/INSTALL.md) for detailed instructions.

**System Requirements:**
- Linux Mint 22.3+ (or Ubuntu 24.04+/Debian-based)
- Python 3.10+
- GTK 3.0

## Usage

### Start the Application

```bash
clipmanx
```

Or find "Clipmanx" in your applications menu.

### System Tray Menu

Click the Clipmanx icon in your system tray to:
- **Select any item** from history to copy to clipboard
- **Clear History** to remove all entries
- **Settings** to configure capture sources
- **Quit** to exit the application

### Configuration

Settings are stored at: `~/.config/clipmanx/settings.json`

Available options:
- `capture_clipboard`: Capture Ctrl+C events (default: true)
- `capture_primary`: Capture X11 PRIMARY selection (default: true)
- `max_items`: Maximum history entries (default: 50)

## Architecture

```
clipmanx/
├── app.py              # Main GTK3 application & UI
├── clipboard.py        # Clipboard monitoring
├── history.py          # History storage & retrieval
└── settings.py         # Configuration management
```

### Icon Adaptation

The tray icon automatically adapts to your system theme:
- **Dark theme** → `icon-white.svg`
- **Light theme** → `icon-black.svg`

This is handled by the `_create_theme_adapted_icon()` function in `app.py`.

## Development

### Setup

```bash
git clone https://github.com/vicsejas/clipmanx.git
cd clipmanx

# Install uv (Python package manager)
# See https://docs.astral.sh/uv/getting-started/
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync
```

### Run from Source

```bash
uv run clipmanx
```

### Build .deb Package

For building Debian packages:
```bash
sudo apt-get install debhelper-compat python3-setuptools python3-all pybuild-plugin-pyproject
dpkg-buildpackage -us -uc -b
```

See [Build Guide](docs/BUILD_GUIDE.md) for detailed instructions.

## Distribution

Clipmanx is distributed via GitHub Releases with automatic `.deb` building.

See [Distribution Guide](docs/DISTRIBUTION.md) for release workflow and instructions.

## Contributing

Contributions welcome! Areas for improvement:
- Additional clipboard sources
- Clipboard search functionality
- Sync across devices
- More theme options

## Author

Victor Sejas - vrsejas@gmail.com

## License

MIT License - See LICENSE file for details

## Attribution

- **Icon**: Clipboard List icon from [Lucide](https://lucide.dev) under [MIT License](https://github.com/lucide-icons/lucide/blob/main/LICENSE)

## Troubleshooting

**Icon not showing?**
```bash
killall clipmanx && clipmanx
```

**Dependencies missing?**
```bash
sudo apt-get install python3-gi gir1.2-gtk-3.0
```

**Can't capture clipboard?**
Check Settings to ensure capture is enabled.

---

Made for Linux Mint by Victor Sejas
