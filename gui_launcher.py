#!/usr/bin/env python3
# MIT License
# Copyright (c) 2025 Artur Grochau
# 
# This file is part of Monitor Layout Manager.
# See the LICENSE file in the root directory for full license text.

"""
Monitor Layout Manager - Self-Contained GUI Launcher
Enhanced entry point with embedded dependency management for seamless user experience
"""

import subprocess
import sys
import os
from pathlib import Path

def get_resources_path():
    """Get the path to the app bundle's Resources folder if running from .app, otherwise project root"""
    if getattr(sys, 'frozen', False):
        # Running from frozen app (py2app, etc.)
        return os.path.dirname(sys.executable)
    
    # Check if we're inside a .app bundle structure
    current_path = Path(__file__).parent.absolute()
    
    # Look for .app bundle structure patterns
    app_contents = current_path / "Contents" / "Resources"
    if app_contents.exists():
        return str(app_contents)
    
    # Check if we're already in Resources folder
    if current_path.name == "Resources":
        return str(current_path)
    
    # Check parent directories for .app structure
    for parent in current_path.parents:
        if parent.name.endswith(".app"):
            resources = parent / "Contents" / "Resources"
            if resources.exists():
                return str(resources)
    
    # Fallback to project root
    return str(current_path)

def ensure_dependencies():
    """Silently install dependencies if needed using embedded requirements.txt"""
    try:
        import tkinter
        import click
        return True  # Dependencies already available
    except ImportError:
        pass
    
    print("🔧 Setting up dependencies for first launch...")
    
    try:
        resources_path = get_resources_path()
        req_file = os.path.join(resources_path, "requirements.txt")
        
        # Find project root (go up from Resources to .app to parent directory)
        project_root = Path(resources_path).parent.parent.parent
        venv_path = project_root / ".venv"
        
        if os.path.exists(req_file):
            print(f"📦 Installing from embedded requirements: {req_file}")
            
            # Create virtual environment if it doesn't exist
            if not venv_path.exists():
                print(f"🐍 Creating virtual environment at: {venv_path}")
                result = subprocess.run([
                    sys.executable, "-m", "venv", str(venv_path)
                ], capture_output=True, text=True)
                
                if result.returncode != 0:
                    print(f"❌ Failed to create virtual environment: {result.stderr}")
                    return False
            
            # Install packages in virtual environment
            venv_python = venv_path / "bin" / "python3"
            if not venv_python.exists():
                venv_python = venv_path / "bin" / "python"
            
            if venv_python.exists():
                print(f"📥 Installing packages with: {venv_python}")
                result = subprocess.run([
                    str(venv_python), "-m", "pip", "install", "-r", req_file
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    print("✅ Dependencies installed successfully!")
                    
                    # Update sys.path to include the new virtual environment
                    site_packages = venv_path / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages"
                    if site_packages.exists():
                        sys.path.insert(0, str(site_packages))
                    
                    return True
                else:
                    print(f"❌ Failed to install dependencies: {result.stderr}")
                    return False
            else:
                print(f"❌ Virtual environment Python not found at: {venv_python}")
                return False
        else:
            print(f"❌ Requirements file not found at: {req_file}")
            
            # Try to run embedded install.sh as fallback
            install_sh = os.path.join(resources_path, "install.sh")
            if os.path.exists(install_sh):
                print("🔧 Running embedded install.sh...")
                # Change to project root before running install.sh
                os.chdir(str(project_root))
                result = subprocess.run(["bash", install_sh], capture_output=True, text=True)
                return result.returncode == 0
            
            return False
            
    except Exception as e:
        print(f"❌ Error during dependency installation: {e}")
        return False

def show_splash_message():
    """Show a simple splash message during setup"""
    try:
        import tkinter as tk
        from tkinter import ttk
        
        splash = tk.Tk()
        splash.title("Monitor Layout Manager")
        splash.geometry("400x150")
        splash.resizable(False, False)
        
        # Center the window
        splash.eval('tk::PlaceWindow . center')
        
        # Create content
        frame = ttk.Frame(splash, padding=20)
        frame.pack(fill="both", expand=True)
        
        ttk.Label(frame, text="🖥️ Monitor Layout Manager", font=("SF Pro", 16, "bold")).pack(pady=10)
        ttk.Label(frame, text="Setting up dependencies for first launch...").pack(pady=5)
        
        progress = ttk.Progressbar(frame, mode='indeterminate')
        progress.pack(pady=10, fill="x")
        progress.start()
        
        splash.update()
        return splash
        
    except ImportError:
        return None

def launch_gui():
    """Launch the main GUI application"""
    try:
        # Ensure the resources path is in sys.path for imports
        resources_path = get_resources_path()
        if resources_path not in sys.path:
            sys.path.insert(0, resources_path)
        
        # Import and launch the advanced GUI
        from advanced_layout_manager import AdvancedMonitorLayoutManager
        
        app = AdvancedMonitorLayoutManager()
        app.run()
        
    except ImportError as e:
        print(f"❌ Failed to import GUI components: {e}")
        print(f"📍 Resources path: {resources_path}")
        print(f"🐍 Python path: {sys.path[:3]}...")  # Show first few paths
        
        # Try alternative import approach
        try:
            # Add the parent directory to handle relative imports
            parent_dir = os.path.dirname(resources_path)
            if parent_dir not in sys.path:
                sys.path.insert(0, parent_dir)
            
            # Try direct import from the Resources directory
            import importlib.util
            gui_module_path = os.path.join(resources_path, "advanced_layout_manager.py")
            
            if os.path.exists(gui_module_path):
                spec = importlib.util.spec_from_file_location("advanced_layout_manager", gui_module_path)
                gui_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(gui_module)
                
                app = gui_module.AdvancedMonitorLayoutManager()
                app.run()
                return
                
        except Exception as e2:
            print(f"❌ Alternative import also failed: {e2}")
        
        # Fallback to basic message
        try:
            import tkinter as tk
            from tkinter import messagebox
            
            root = tk.Tk()
            root.withdraw()
            
            messagebox.showerror(
                "Monitor Layout Manager", 
                f"Failed to launch GUI: {e}\n\nPlease check that all dependencies are installed.\n\nResources: {resources_path}"
            )
        except ImportError:
            print("❌ GUI components not available. Please run install.sh manually.")

def main():
    """Main entry point with dependency management"""
    
    # Check if dependencies are available
    try:
        import tkinter
        import click
        # Dependencies available, launch directly
        launch_gui()
        return
        
    except ImportError:
        pass
    
    # Dependencies missing, show splash and install
    splash = show_splash_message()
    
    try:
        if ensure_dependencies():
            if splash:
                splash.destroy()
            
            print("🚀 Launching GUI...")
            launch_gui()
        else:
            if splash:
                splash.destroy()
                
            # Show error dialog
            try:
                import tkinter as tk
                from tkinter import messagebox
                
                root = tk.Tk()
                root.withdraw()
                
                messagebox.showerror(
                    "Monitor Layout Manager", 
                    "Failed to install required dependencies.\n\n"
                    "Please ensure you have an internet connection and try again.\n"
                    "You can also run install.sh manually in Terminal."
                )
            except ImportError:
                print("❌ Failed to install dependencies and GUI not available.")
                
    except KeyboardInterrupt:
        if splash:
            splash.destroy()
        print("\n⚠️  Setup cancelled by user")

if __name__ == "__main__":
    main()
