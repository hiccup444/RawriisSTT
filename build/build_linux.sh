#!/usr/bin/env bash
set -e

# Resolve paths relative to this script, regardless of where it's run from
BUILDDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJROOT="$(dirname "$BUILDDIR")"

echo "============================================================"
echo " RawriisSTT -- Linux build"
echo "============================================================"
echo

# Install build dependencies
python3 -m pip install --quiet pyinstaller pillow openvr
if [ $? -ne 0 ]; then
    echo "ERROR: pip failed. Make sure Python 3 is installed and on your PATH."
    exit 1
fi

# Build — distpath and workpath anchored to the project root (matches Windows layout)
python3 -m PyInstaller "$BUILDDIR/windows.spec" \
    --clean \
    --noconfirm \
    --distpath "$PROJROOT/dist" \
    --workpath "$BUILDDIR/work"

echo
echo "============================================================"
echo " Build complete!"
echo " Output: dist/RawriisSTT/RawriisSTT"
echo "============================================================"
