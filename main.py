#!/usr/bin/env python3
"""
Monitor Layout Manager - Unified Entry Point
A sophisticated macOS monitor layout manager with visual configuration.
"""

import sys
import os
import subprocess

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def auto_install_dependencies():
    """Auto-install dependencies if missing (beginner-friendly approach)."""
    try:
        import tkinter
        import click
        # If both imports succeed, dependencies are available
        return True
    except ImportError:
        print("🔧 Installing missing dependencies...")
        try:
            # Run install.sh to set up everything
            subprocess.run(["./install.sh"], check=True, cwd=os.path.dirname(os.path.abspath(__file__)))
            print("✅ Dependencies installed successfully!")
            # Restart the script with the same arguments
            os.execv(sys.executable, [sys.executable] + sys.argv)
        except subprocess.CalledProcessError:
            print("❌ Failed to install dependencies automatically.")
            print("💡 Please run: ./install.sh")
            sys.exit(1)
        except FileNotFoundError:
            print("❌ install.sh not found. Please download the complete project.")
            sys.exit(1)

def check_setup():
    """Validate that setup is complete before launching."""
    # First try auto-installation of dependencies
    auto_install_dependencies()
    
    # Check if .venv exists
    if not os.path.exists('.venv'):
        print("❗ Setup not complete. Run `./install.sh` first.")
        sys.exit(1)
    
    # Warn if virtual environment is not activated (optional check)
    if not os.getenv("VIRTUAL_ENV") and os.path.exists('.venv'):
        print("⚠️  Virtual environment not activated.")
        print("💡 For best results, run: source .venv/bin/activate")
        print("   Or use: .venv/bin/python main.py")
        print("")

def launch_gui():
    """Launch the advanced GUI interface."""
    check_setup()
    try:
        from gui.advanced_layout_manager import AdvancedMonitorLayoutManager
        app = AdvancedMonitorLayoutManager()
        app.run()
    except ImportError as e:
        print(f"❌ GUI Error: {e}")
        print("💡 Try running: ./install.sh")
        print("💡 Install GUI dependencies: brew install python-tk")
        print("🔧 For CLI usage, run: python main.py --cli")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

def launch_cli():
    """Launch the CLI interface."""
    check_setup()
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

def show_help():
    """Show help information."""
    print("🖥️  Monitor Layout Manager")
    print("")
    print("1️⃣  Launch GUI:  python3 main.py")
    print("2️⃣  Launch CLI:  python3 main.py --cli")
    print("")
    print("Examples:")
    print("  python3 main.py --cli detect     # Detect displays")
    print("  python3 main.py --cli layouts    # List saved layouts")

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
        # Interactive menu when no args
        print("🖥️  Monitor Layout Manager")
        print("")
        print("1️⃣  Launch GUI")
        print("2️⃣  Launch CLI") 
        print("")
        try:
            choice = input("Choose option (1/2, or Enter for GUI): ").strip()
            if choice == '2':
                launch_cli()
            else:
                launch_gui()
        except (KeyboardInterrupt, EOFError):
            print("\n👋 Goodbye!")
            return
    else:
        # Default to GUI for best user experience
        launch_gui()

if __name__ == "__main__":
    main()
