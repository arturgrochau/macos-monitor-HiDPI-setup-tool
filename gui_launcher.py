#!/usr/bin/env python3
# MIT License
# Copyright (c) 2025 Artur Grochau
# 
# This file is part of Monitor Layout Manager.
# See the LICENSE file in the root directory for full license text.

"""
Monitor Layout Manager - Fixed GUI Launcher
Resolves resource paths properly and prevents Tkinter crashes
"""

import os
import sys
import subprocess
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox

def app_resources_dir():
    """Get the Resources directory path for both .app bundle and dev mode"""
    # Inside .app bundle -> .../My.app/Contents/Resources
    if getattr(sys, 'frozen', False):
        return os.path.join(os.path.dirname(sys.executable), "..", "Resources")
    
    # Dev mode -> project root (where this script is located)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # If we're in .app/Contents/Resources, return current directory
    if "Contents/Resources" in script_dir:
        return script_dir
    
    return script_dir

def run_installer_if_needed():
    """Run the installer if dependencies are missing"""
    res_dir = app_resources_dir()
    installer = os.path.join(res_dir, "install.sh")
    req_file = os.path.join(res_dir, "requirements.txt")
    
    # Create log directory and file
    log_dir = os.path.expanduser("~/Library/Logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "MonitorLayoutManager.log")
    
    with open(log_file, "a") as f:
        f.write(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] BOOT: Resources dir={res_dir}\n")
        f.write(f"Looking for installer at: {installer}\n")
        f.write(f"Looking for requirements at: {req_file}\n")
    
    if not os.path.exists(installer):
        error_msg = f"Dependencies missing and install.sh not found at {installer}"
        with open(log_file, "a") as f:
            f.write(f"ERROR: {error_msg}\n")
        print(error_msg)
        return False, error_msg
    
    if not os.path.exists(req_file):
        error_msg = f"Requirements file not found at {req_file}"
        with open(log_file, "a") as f:
            f.write(f"ERROR: {error_msg}\n")
        return False, error_msg
    
    # Ensure installer is executable
    try:
        os.chmod(installer, 0o755)
    except Exception as e:
        with open(log_file, "a") as f:
            f.write(f"WARNING: Could not make installer executable: {e}\n")
    
    try:
        with open(log_file, "a") as f:
            f.write(f"Running installer: /bin/bash {installer}\n")
        
        # Run installer
        result = subprocess.run(["/bin/bash", installer], 
                              cwd=res_dir, 
                              capture_output=True, 
                              text=True,
                              timeout=300)  # 5 minute timeout
        
        with open(log_file, "a") as f:
            f.write(f"Installer exit code: {result.returncode}\n")
            if result.stdout:
                f.write(f"STDOUT:\n{result.stdout}\n")
            if result.stderr:
                f.write(f"STDERR:\n{result.stderr}\n")
        
        if result.returncode == 0:
            return True, "Installation completed successfully"
        else:
            return False, f"Installer failed with code {result.returncode}:\n{result.stderr[:500]}"
            
    except subprocess.TimeoutExpired:
        error_msg = "Installer timed out after 5 minutes"
        with open(log_file, "a") as f:
            f.write(f"ERROR: {error_msg}\n")
        return False, error_msg
    except Exception as e:
        error_msg = f"Failed to run installer: {e}"
        with open(log_file, "a") as f:
            f.write(f"ERROR: {error_msg}\n")
        return False, error_msg

class NonBlockingSplash:
    """Non-blocking splash screen with progress bar"""
    
    def __init__(self, root):
        self.root = root
        self.splash = None
        self.progress_bar = None
        self.status_label = None
        
    def show(self, message="Preparing Monitor Layout Manager..."):
        """Show the splash screen"""
        self.splash = tk.Toplevel(self.root)
        self.splash.overrideredirect(True)
        self.splash.title("Loading")
        
        # Create content frame
        frame = ttk.Frame(self.splash, padding="30")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Status label
        self.status_label = ttk.Label(frame, text=message, font=("SF Pro Text", 12))
        self.status_label.pack(pady=(0, 15))
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(frame, mode="indeterminate", length=250)
        self.progress_bar.pack(pady=(0, 15))
        self.progress_bar.start(8)
        
        # Size and center the splash
        self.splash.update_idletasks()
        width = 350
        height = 120
        x = (self.splash.winfo_screenwidth() // 2) - (width // 2)
        y = (self.splash.winfo_screenheight() // 2) - (height // 2)
        self.splash.geometry(f"{width}x{height}+{x}+{y}")
        
        self.splash.lift()
        self.splash.attributes("-topmost", True)
        self.splash.update()
        
    def update_status(self, message):
        """Update the status message"""
        if self.splash and self.splash.winfo_exists() and self.status_label:
            self.status_label.config(text=message)
            self.splash.update()
    
    def hide(self):
        """Hide the splash screen"""
        if self.splash and self.splash.winfo_exists():
            if self.progress_bar:
                self.progress_bar.stop()
            self.splash.destroy()
            self.splash = None

def build_main_gui(root):
    """Build the main GUI interface"""
    try:
        # Add the project root to Python path for imports
        res_dir = app_resources_dir()
        if res_dir not in sys.path:
            sys.path.insert(0, res_dir)
        
        # Log GUI startup
        log_file = os.path.expanduser("~/Library/Logs/MonitorLayoutManager.log")
        with open(log_file, "a") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] GUI: Starting main interface\n")
        
        # Import the main GUI
        from gui.advanced_layout_manager import MonitorLayoutManager
        
        # Hide the root window
        root.withdraw()
        
        # Create and run the main application
        app = MonitorLayoutManager()
        
        with open(log_file, "a") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] GUI: Application created successfully\n")
        
        app.run()
        
    except ImportError as e:
        error_msg = f"Could not load GUI components:\n{e}\n\nPlease check that all files are present."
        messagebox.showerror("Import Error", error_msg)
        
        log_file = os.path.expanduser("~/Library/Logs/MonitorLayoutManager.log")
        with open(log_file, "a") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] GUI: Import error - {e}\n")
        
        root.quit()
    except Exception as e:
        error_msg = f"Failed to start GUI:\n{e}"
        messagebox.showerror("Startup Error", error_msg)
        
        log_file = os.path.expanduser("~/Library/Logs/MonitorLayoutManager.log")
        with open(log_file, "a") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] GUI: Startup error - {e}\n")
        
        root.quit()

def show_error_and_quit(root, message):
    """Show error dialog and quit"""
    messagebox.showerror("Setup Error", message)
    root.quit()

def boot_sequence(root, splash):
    """Background boot sequence"""
    try:
        # Update splash
        root.after(0, lambda: splash.update_status("Checking dependencies..."))
        time.sleep(0.5)
        
        # Check if we need to run installer
        success, message = run_installer_if_needed()
        
        if success:
            root.after(0, lambda: splash.update_status("Loading interface..."))
            time.sleep(0.5)
            # Close splash and build main UI
            root.after(0, lambda: (splash.hide(), build_main_gui(root)))
        else:
            # Show error and quit
            root.after(0, lambda: (splash.hide(), show_error_and_quit(root, message)))
            
    except Exception as e:
        error_msg = f"Boot sequence failed: {e}"
        root.after(0, lambda: (splash.hide(), show_error_and_quit(root, error_msg)))

def main():
    """Main application entry point with non-blocking setup"""
    
    print("🖥️  Monitor Layout Manager v1.4.0 - Fixed OOTB Experience")
    
    # Create root window (hidden initially)
    root = tk.Tk()
    root.title("Monitor Layout Manager")
    root.withdraw()  # Hide until ready
    
    # Create and show splash screen
    splash = NonBlockingSplash(root)
    splash.show()
    
    # Start background boot sequence
    boot_thread = threading.Thread(target=boot_sequence, args=(root, splash), daemon=True)
    boot_thread.start()
    
    # Start main loop
    root.mainloop()

if __name__ == "__main__":
    main()
