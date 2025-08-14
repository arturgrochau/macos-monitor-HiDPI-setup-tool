#!/bin/bash
"""
Build Script for Monitor Layout Manager
Builds standalone macOS app bundle from source
"""

set -e  # Exit on any error

echo "🏗️  Building Monitor Layout Manager..."
echo "=================================="

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build dist Monitor-Layout-Manager-v*.zip dist-package

# Activate virtual environment
echo "🐍 Activating virtual environment..."
if [[ "$SHELL" == *"fish" ]]; then
    source .venv/bin/activate.fish
else
    source .venv/bin/activate
fi

# Ensure all dependencies are installed
echo "📦 Installing/updating dependencies..."
pip install -q py2app Pillow

# Create the app icon if it doesn't exist
if [ ! -f "app_icon.icns" ]; then
    echo "🎨 Creating app icon..."
    python create_icon.py
fi

# Build the macOS app bundle
echo "🏗️  Building macOS app bundle..."
python setup.py py2app --quiet

# Create deployment package
echo "📦 Creating deployment package..."
./create_package.sh

# Show results
echo ""
echo "✅ Build completed successfully!"
echo "📱 App bundle: dist/Monitor Layout Manager.app"
echo "📦 Distribution ZIP: Monitor-Layout-Manager-v1.0.0-macOS.zip"
echo "📏 Size: $(ls -lah Monitor-Layout-Manager-v1.0.0-macOS.zip | awk '{print $5}')"
echo ""
echo "🚀 Ready for:"
echo "   • Local testing: open 'dist/Monitor Layout Manager.app'"
echo "   • Distribution: Upload Monitor-Layout-Manager-v1.0.0-macOS.zip to GitHub Releases"
echo "   • User download: Users extract ZIP and double-click the .app"
