#!/usr/bin/env bash
# Build Monitor Layout Manager.app via py2app.
# Usage: ./build_app.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Installing build dependencies..."
pip install -r requirements-dev.txt --quiet

echo "Cleaning previous build artifacts..."
rm -rf build/ dist/

echo "Building app bundle..."
python setup.py py2app 2>&1

APP="dist/Monitor Layout Manager.app"
if [ -d "$APP" ]; then
    echo ""
    echo "Build successful: $APP"
    du -sh "$APP"
else
    echo "Build failed — check output above." >&2
    exit 1
fi
