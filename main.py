#!/usr/bin/env python3
"""
Monitor Layout Manager - Unified Entry Point
A sophisticated macOS monitor layout manager with visual configuration.
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def launch_gui():
    """Launch the advanced GUI interface."""
    try:
        from gui.advanced_layout_manager import AdvancedMonitorLayoutManager
        app = AdvancedMonitorLayoutManager()
        app.run()
    except ImportError as e:
        print(f"❌ GUI Error: {e}")
        print("💡 For CLI usage, run: python main.py --cli")
        print("📦 Install GUI dependencies: pip install pillow")
        print("🍺 Install tkinter: brew install python-tk")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

def launch_cli():
    """Launch the CLI interface."""
    try:
        # Use subprocess to call the CLI module directly
        import subprocess
        
        # Get all arguments except the first (script name) and remove --cli
        args = [arg for arg in sys.argv[1:] if arg != '--cli']
        
        # Build command for CLI module
        cmd = [sys.executable, '-m', 'cli'] + args
        
        # Execute CLI module
        result = subprocess.run(cmd, cwd=os.path.dirname(os.path.abspath(__file__)))
        sys.exit(result.returncode)
        
    except ImportError as e:
        print(f"❌ CLI Error: {e}")
        print("📦 Install dependencies: pip install click rich colorama")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

def main():
    """Main entry point - dispatches to GUI or CLI based on arguments."""
    # Simple argument parsing
    if len(sys.argv) > 1 and '--cli' in sys.argv:
        launch_cli()
    elif len(sys.argv) > 1 and '--gui' in sys.argv:
        launch_gui()
    elif len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h']:
        print("🖥️  Monitor Layout Manager")
        print("")
        print("Usage:")
        print("  python main.py           # Launch GUI (default)")
        print("  python main.py --gui     # Launch GUI explicitly")  
        print("  python main.py --cli     # Launch CLI mode")
        print("  python main.py --cli detect  # CLI with commands")
        print("")
        print("Shortcuts:")
        print("  python -m cli            # Direct CLI access")
        print("  scripts/monitor-cli      # Shell wrapper")
        print("  scripts/monitor-gui      # GUI launcher")
    else:
        # Default to GUI
        launch_gui()

if __name__ == "__main__":
    main()
