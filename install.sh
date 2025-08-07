#!/bin/bash
# Monitor Layout Manager - Universal Installation Script
# Compatible with all shells: bash, zsh, fish

set -e  # Exit on any error

echo "�️  Monitor Layout Manager - Installation"
echo "========================================"

# Check if we're on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ This tool only works on macOS"
    exit 1
fi

echo ""
echo "📦 Installing Dependencies..."

# Install displayplacer via Homebrew
if ! command -v displayplacer &> /dev/null; then
    echo "  📥 Installing displayplacer..."
    if command -v brew &> /dev/null; then
        brew install jakehilborn/jakehilborn/displayplacer
    else
        echo "  ❌ Homebrew not found. Please install Homebrew first:"
        echo "     /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        exit 1
    fi
else
    echo "  ✅ displayplacer already installed"
fi

# Check and suggest tkinter for GUI
echo ""
echo "🎨 GUI Dependencies..."
python3 -c "import tkinter" 2>/dev/null && echo "  ✅ tkinter available" || {
    echo "  ⚠️  tkinter not found - GUI will not work"
    echo "  📥 Install with: brew install python-tk"
}

echo ""
echo "🐍 Python Virtual Environment..."

# Create virtual environment
if [ ! -d ".venv" ]; then
    echo "  📦 Creating virtual environment..."
    python3 -m venv .venv
else
    echo "  ✅ Virtual environment exists"
fi

# Activate and install dependencies
echo "  📥 Installing Python packages..."
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt

echo ""
echo "🖥️  HiDPI Display Setup..."

# Set up HiDPI overrides if they exist
if [ -d "overrides" ]; then
    echo "  📁 Installing HiDPI overrides..."
    sudo mkdir -p /Library/Displays/Contents/Resources/Overrides/DisplayVendorID-610
    if [ -f "overrides/DisplayVendorID-610/DisplayProductID-31333031.plist" ]; then
        sudo cp overrides/DisplayVendorID-610/DisplayProductID-31333031.plist /Library/Displays/Contents/Resources/Overrides/DisplayVendorID-610/
        sudo chown root:wheel /Library/Displays/Contents/Resources/Overrides/DisplayVendorID-610/DisplayProductID-31333031.plist
        sudo chmod 644 /Library/Displays/Contents/Resources/Overrides/DisplayVendorID-610/DisplayProductID-31333031.plist
        
        echo "  🧹 Clearing display caches..."
        sudo rm -rf /Library/Preferences/com.apple.windowserver*.plist 2>/dev/null || true
        sudo rm -rf ~/Library/Preferences/ByHost/com.apple.windowserver* 2>/dev/null || true
    fi
else
    echo "  ⚠️  No HiDPI overrides found - skipping"
fi

echo ""
echo "🔗 Setting up shell-neutral entry points..."
chmod +x scripts/monitor-cli scripts/monitor-gui 2>/dev/null || true

echo ""
echo "✅ Installation Complete!"
echo ""
echo "🚀 Quick Start:"
echo "  python3 main.py              # Launch GUI"
echo "  python3 main.py --cli        # Launch CLI"  
echo "  python3 -m cli detect        # Direct CLI"
echo "  ./scripts/monitor-cli detect # Shell wrapper"
echo "  ./scripts/monitor-gui        # GUI launcher"
echo ""

# Detect current shell and show specific integration
if [ -n "$FISH_VERSION" ]; then
    echo "🐟 Detected Fish Shell:"
    echo "  fish scripts/install-fish.fish    # Full fish integration"
elif [ -n "$ZSH_VERSION" ]; then
    echo "🚀 Detected Zsh Shell - Ready to use!"
elif [ -n "$BASH_VERSION" ]; then
    echo "🐚 Detected Bash Shell - Ready to use!"
else
    echo "🔧 Shell detected - Ready to use!"
fi

echo ""
if [ -d "overrides" ]; then
    echo "⚠️  Reboot required for HiDPI changes to take effect"
else
    echo "✨ Ready to use immediately!"
fi
