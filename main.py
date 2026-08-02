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
        print("💡 Install GUI dependencies: brew install python-tk")
        print("🔧 For CLI usage, run: python main.py --cli")
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
        result = subprocess.run(cmd, cwd=os.path.dirname(os.path.abspath(__file__)), check=False)
        sys.exit(result.returncode)
        
    except ImportError as e:
        print(f"❌ CLI Error: {e}")
        print("📦 Install dependencies: pip install click")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

def show_help():
    """Show help information."""
    print("🖥️  Monitor Layout Manager")
    print("")
    print("1️⃣  Launch GUI:  python3 main.py")
    print("2️⃣  Launch CLI:  python3 main.py --cli")
    print("")
    print("Examples:")
    print("  python3 main.py --cli detect          # Detect displays")
    print("  python3 main.py --cli list-layouts    # List saved layouts")

def main():
    """Main entry point - dispatches to GUI or CLI based on arguments."""
    # Check for help first
    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h', 'help']:
        show_help()
        return
    
    # Check for CLI mode
    if len(sys.argv) > 1 and '--cli' in sys.argv:
        launch_cli()
    elif len(sys.argv) > 1 and '--gui' in sys.argv:
        launch_gui()
    elif len(sys.argv) == 1:
        # No args: launch the GUI (use --cli for the command-line interface)
        launch_gui()
    else:
        # Default to GUI for best user experience
        launch_gui()

if __name__ == "__main__":
    main()
