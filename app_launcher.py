#!/usr/bin/env python3
"""
Monitor Layout Manager - macOS App Launcher
Standalone app entry point for py2app bundle.
"""

import sys
import os
import subprocess
from pathlib import Path

def main():
    """Main app launcher - always starts GUI mode."""
    try:
        # Get the app bundle's Resources directory
        if getattr(sys, 'frozen', False):
            # Running as py2app bundle
            bundle_dir = Path(sys.executable).parent.parent
            resources_dir = bundle_dir / 'Resources'
        else:
            # Running in development
            resources_dir = Path(__file__).parent
        
        # Add the resources directory to Python path
        sys.path.insert(0, str(resources_dir))
        
        # Change to the resources directory
        os.chdir(str(resources_dir))
        
        # Import and launch the GUI
        from gui.advanced_layout_manager import AdvancedMonitorLayoutManager
        
        print("🖥️ Launching Monitor Layout Manager...")
        app = AdvancedMonitorLayoutManager()
        app.run()
        
    except ImportError as e:
        # Fallback error dialog
        import tkinter as tk
        from tkinter import messagebox
        
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Monitor Layout Manager Error", 
            f"Failed to import required modules: {e}\n\nPlease ensure all dependencies are installed."
        )
        sys.exit(1)
        
    except Exception as e:
        # General error dialog
        import tkinter as tk
        from tkinter import messagebox
        
        root = tk.Tk() 
        root.withdraw()
        messagebox.showerror(
            "Monitor Layout Manager Error",
            f"An unexpected error occurred: {e}\n\nPlease check your installation."
        )
        sys.exit(1)

if __name__ == "__main__":
    main()
