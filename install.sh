#!/bin/bash
# Monitor Layout Manager - Universal Installation Script

set -e  # Exit on any error

echo "�️  echo ""
echo "✅ Installation Complete!"
echo ""
echo "🚀 Quick Start:"
echo "  1️⃣ Launch GUI:    ./monitor-layout"
echo "  2️⃣ Launch CLI:    ./monitor-layout --cli detect"  
echo "  3️⃣ Global CLI:    monitor-layout (after restart)"
echo ""
echo "💡 The GUI lets you drag monitors around to position them."
echo ""

# Optional auto-launch prompt
read -p "🎯 Launch GUI now? (y/N): " launch_guianager - Installation"
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
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] INSTALL: Installed displayplacer via Homebrew" >> docs/DEVELOPMENT_LOG.md
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
.venv/bin/pip install --upgrade pip > /dev/null 2>&1
if .venv/bin/pip install -r requirements.txt > /dev/null 2>&1; then
    echo "  ✅ Dependencies installed successfully"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] INSTALL: Python dependencies installed from requirements.txt" >> docs/DEVELOPMENT_LOG.md
else
    echo "  ❌ Failed to install dependencies"
    echo "  💡 Check your internet connection and try again"
    exit 1
fi

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
echo "🔗 Setting up global CLI access..."
# Optional global CLI linking
if [ ! -d "~/bin" ]; then
    mkdir -p ~/bin
fi
if [ -f ~/bin/monitor-layout ]; then
    rm ~/bin/monitor-layout 2>/dev/null || true
fi
ln -sf "$(pwd)/scripts/monitor-cli" ~/bin/monitor-layout

# Add ~/bin to PATH if not already there
if [[ ":$PATH:" != *":$HOME/bin:"* ]]; then
    SHELL_NAME=$(basename "$SHELL")
    case "$SHELL_NAME" in
        "fish")
            echo 'set -gx PATH $HOME/bin $PATH' >> ~/.config/fish/config.fish 2>/dev/null || true
            echo "✅ Added ~/bin to PATH in Fish config"
            ;;
        "zsh")
            echo 'export PATH="$HOME/bin:$PATH"' >> ~/.zshrc 2>/dev/null || true
            echo "✅ Added ~/bin to PATH in .zshrc"
            ;;
        *)
            echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bash_profile 2>/dev/null || true
            echo "✅ Added ~/bin to PATH in .bash_profile"
            ;;
    esac
fi

echo ""
echo "🔗 Setting up unified entry point..."
chmod +x monitor-layout scripts/monitor-cli scripts/monitor-gui 2>/dev/null || true

echo ""
echo "🎉 Installation Complete! 🎉"
echo ""
echo "✅ Virtual environment created and dependencies installed"
echo "✅ Scripts made executable and CLI access configured" 
echo "✅ Ready to launch Monitor Layout Manager"
echo ""
echo "🚀 Quick Start:"
echo "  1️⃣ Launch GUI:    ./monitor-layout"
echo "  2️⃣ Launch CLI:    ./monitor-layout --cli detect"  
echo "  3️⃣ Global CLI:    monitor-layout (after restart)"
echo ""
echo "💡 The GUI lets you drag monitors around to position them."
echo ""

# Optional auto-launch prompt
read -p "🎯 Launch GUI now? (y/N): " launch_gui
if [[ "$launch_gui" =~ ^[Yy]$ ]]; then
    echo "� Launching Monitor Layout Manager..."
    ./monitor-layout
else
    echo "👋 Run './monitor-layout' when ready!"
fi
