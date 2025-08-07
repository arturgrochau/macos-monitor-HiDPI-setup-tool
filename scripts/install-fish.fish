#!/usr/bin/env fish
# Simple installation script for Monitor Layout Manager

function install_monitor_layout_manager
    echo "� Installing Monitor Layout Manager..."
    echo
    
    # Check if we're in the right directory
    if not test -f "cli/advanced_cli.py"
        echo "❌ Error: Please run this script from the monitor-setup-tool project directory"
        return 1
    end
    
    # Create virtual environment
    echo "� Setting up Python environment..."
    if not test -d ".venv"
        python3 -m venv .venv
    end
    
    # Install dependencies
    echo "� Installing dependencies..."
    .venv/bin/pip install click rich colorama pillow
    
    # Check for displayplacer
    echo "🔍 Checking for displayplacer..."
    if command -q displayplacer
        echo "✅ displayplacer is already installed"
    else if command -q brew
        echo "📦 Installing displayplacer..."
        brew install jakehilborn/jakehilborn/displayplacer
    else
        echo "⚠️  Please install displayplacer manually:"
        echo "  brew install jakehilborn/jakehilborn/displayplacer"
    end
    
    # Make scripts executable
    chmod +x monitor-layout.sh
    chmod +x gui-fish.fish
    chmod +x ml-fish
    
    echo
    echo "🎉 Installation complete!"
    echo
    echo "Usage:"
    echo "  python3 main.py               # Launch GUI"
    echo "  python3 -m cli detect        # CLI: detect displays"
    echo "  python3 -m cli save -n work  # CLI: save layout"
    echo "  ./monitor-layout.sh           # Universal launcher (GUI)"
    echo "  ./monitor-layout.sh cli detect # Universal launcher (CLI)"
    echo "  ./ml-fish detect             # Fish wrapper (CLI)"
end

# Run the installation
install_monitor_layout_manager
