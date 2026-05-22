# Building Clipmanx Locally

Guide for developers building from source for testing and development.

## Quick Start

```bash
cd /path/to/clipmanx

# Install build dependencies (one-time)
sudo apt-get install debhelper-compat python3-setuptools python3-all pybuild-plugin-pyproject

# Build .deb package
bash build.sh

# Install locally (script will suggest the command)
```

For detailed installation instructions, see [INSTALL.md](INSTALL.md).

---

## Development Workflow

### Test Before Building

To quickly test the app without building a package:

```bash
# Install uv (optional, for development only)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies and run
uv sync
uv run clipmanx
```

**Note**: `uv` is only for development. The `.deb` package doesn't require it.

---

### Using the Build Script

The `build.sh` script automates the build process:

```bash
bash build.sh
```

This:
1. Checks dependencies
2. Cleans previous builds
3. Builds the `.deb` package
4. Places artifacts in `/build`

Output files:
```
build/clipmanx_0.1.0-1_all.deb    ← Install this
build/clipmanx_0.1.0-1.changes    ← Metadata
build/clipmanx_0.1.0-1.buildinfo  ← Build info
```

### Manual Build (Advanced)

```bash
cd /path/to/clipmanx
dpkg-buildpackage -us -uc -b
mkdir -p build
mv ../clipmanx_*.deb build/
```

---

## How the Build Works

`dpkg-buildpackage`:
1. Reads `debian/control` (package metadata)
2. Executes `debian/rules` (build instructions)
3. Stages files to temporary directory
4. Creates `.deb` (compressed archive)
5. Places `.deb` in parent directory

---

## Releases

To create a GitHub release, see [DISTRIBUTION.md](DISTRIBUTION.md).

**Last Updated**: May 21, 2026
