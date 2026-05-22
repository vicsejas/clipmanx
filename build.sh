#!/bin/sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BUILD_DIR="$SCRIPT_DIR/build"

echo "Building Clipmanx .deb package"
echo "=============================="

if ! command -v dpkg-buildpackage >/dev/null 2>&1; then
    echo "Error: dpkg-buildpackage not found"
    echo "Install with: sudo apt-get install debhelper-compat python3-setuptools python3-all pybuild-plugin-pyproject"
    exit 1
fi

mkdir -p "$BUILD_DIR"
echo "Build directory: $BUILD_DIR"

echo "Cleaning previous builds..."
rm -f "$BUILD_DIR"/*.deb "$BUILD_DIR"/*.changes "$BUILD_DIR"/*.buildinfo

echo "Building package..."
cd "$SCRIPT_DIR"
dpkg-buildpackage -us -uc -b

echo "Moving artifacts to build directory..."
deb_count=0
for f in "$SCRIPT_DIR"/../clipmanx_*.deb; do
    if [ -f "$f" ]; then
        mv "$f" "$BUILD_DIR/"
        deb_count=$((deb_count + 1))
    fi
done

if [ "$deb_count" -eq 0 ]; then
    echo "Error: Build failed, no .deb file found"
    exit 1
fi

for f in "$SCRIPT_DIR"/../clipmanx_*.changes "$SCRIPT_DIR"/../clipmanx_*.buildinfo; do
    [ -f "$f" ] && mv "$f" "$BUILD_DIR/"
done

echo ""
echo "Build complete! Artifacts in $BUILD_DIR:"
ls -lh "$BUILD_DIR"/*.deb

echo ""
echo "To install:"
echo "  sudo apt-get install -y $BUILD_DIR/clipmanx_*.deb"
echo ""
echo "To clean build artifacts:"
echo "  rm -rf $BUILD_DIR"
