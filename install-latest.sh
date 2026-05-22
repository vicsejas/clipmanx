#!/bin/bash

set -e

echo "Clipmanx Installer for Linux Mint"
echo "===================================="

# Check if running on Linux Mint
if ! grep -q "Linux Mint\|Ubuntu\|Debian" /etc/os-release 2>/dev/null; then
    echo "Warning: This installer is optimized for Debian-based systems (Linux Mint, Ubuntu, etc.)"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if root
if [ "$EUID" -ne 0 ]; then
    echo "Error: This installer must be run with sudo"
    echo ""
    echo "Usage: sudo bash install-latest.sh"
    exit 1
fi

echo "Installing dependencies..."
apt-get update
apt-get install -y python3-gi gir1.2-gtk-3.0 wget curl || {
    echo "Error: Failed to install dependencies"
    exit 1
}

REPO="${GITHUB_REPO:-vicsejas/clipmanx}"
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

echo "Downloading latest release..."
RELEASE_DATA=$(curl -s "https://api.github.com/repos/$REPO/releases/latest")

if [ -z "$RELEASE_DATA" ] || echo "$RELEASE_DATA" | grep -q '"message"'; then
    echo "Error: Could not fetch release information from GitHub"
    exit 1
fi

LATEST_RELEASE=$(echo "$RELEASE_DATA" | grep -o '"tag_name"[[:space:]]*:[[:space:]]*"[^"]*"' | cut -d'"' -f4)

if [ -z "$LATEST_RELEASE" ]; then
    echo "Error: Could not find latest release"
    exit 1
fi

echo "   Found version: $LATEST_RELEASE"

# Get the actual .deb filename from the release
DEB_FILENAME=$(echo "$RELEASE_DATA" | grep -o '"name"[[:space:]]*:[[:space:]]*"clipmanx_[^"]*\.deb' | cut -d'"' -f4 | head -1)

if [ -z "$DEB_FILENAME" ]; then
    echo "Error: Could not find .deb filename in release"
    exit 1
fi

# Download .deb file
DEB_URL="https://github.com/$REPO/releases/download/$LATEST_RELEASE/$DEB_FILENAME"
if ! wget -O "$TEMP_DIR/clipmanx.deb" "$DEB_URL"; then
    echo "Error: Failed to download .deb package from $DEB_URL"
    exit 1
fi

echo "Installing clipmanx..."
apt-get install -y "$TEMP_DIR/clipmanx.deb" || {
    echo "Error: Failed to install clipmanx package"
    exit 1
}

echo ""
echo "Clipmanx $LATEST_RELEASE installed successfully!"
echo ""
echo "Next steps:"
echo "  - Run 'clipmanx' from terminal to start the app"
echo "  - Find 'Clipmanx' in your applications menu"
echo "  - It will appear in your system tray"
echo ""
echo "To uninstall: sudo apt-get remove clipmanx"
