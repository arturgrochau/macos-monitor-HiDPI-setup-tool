#!/usr/bin/env python3
# MIT License
# Copyright (c) 2025 Artur Grochau
# 
# This file is part of Monitor Layout Manager.
# See the LICENSE file in the root directory for full license text.

"""
Monitor Layout Manager - Ultimate OOTB GUI Launcher
Fixes all modal crashes, bundles install.sh internally, perfect UX
"""

import subprocess
import sys
import os
import threading
import time
from pathlib import Path

try:
    import tkinter as tk
    from tkinter import ttk
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False

class NonBlockingSplash:
    """Non-blocking splash screen that prevents modal crashes"""
    
    def __init__(self):
        self.window = None
        self.progress = None
        self.status_label = None
        self.destroyed = False
        self._setup_complete = False
        
    def create_and_show(self):
        """Create and show splash screen safely"""
        if not TKINTER_AVAILABLE:
            print("🖥️  Monitor Layout Manager - Console Mode")
            return
            
        try:
            # Create root window first
            self.window = tk.Tk()
            self.window.title("Monitor Layout Manager")
            self.window.geometry("450x250")
            self.window.resizable(False, False)
            
            # Center the window
            self.window.update_idletasks()
            x = (self.window.winfo_screenwidth() // 2) - (450 // 2)
            y = (self.window.winfo_screenheight() // 2) - (250 // 2)
            self.window.geometry(f"450x250+{x}+{y}")
            
            # Set window icon if available
            icon_path = Path(__file__).parent / "AppIcon.icns"
            if icon_path.exists():
                try:
                    self.window.iconbitmap(str(icon_path))
                except:
                    pass
            
            # Main frame with padding
            main_frame = ttk.Frame(self.window, padding="30")
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            # Header with icon
            header_frame = ttk.Frame(main_frame)
            header_frame.pack(fill=tk.X, pady=(0, 20))
            
            ttk.Label(header_frame, text="🖥️", font=('SF Pro Display', 32)).pack()
            ttk.Label(header_frame, text="Monitor Layout Manager", 
                     font=('SF Pro Display', 18, 'bold')).pack(pady=(10, 0))
            ttk.Label(header_frame, text="v1.3.0", 
                     font=('SF Pro Display', 12), foreground='gray').pack()
            
            # Status and progress section
            status_frame = ttk.Frame(main_frame)
            status_frame.pack(fill=tk.X, pady=(0, 20))
            
            self.status_label = ttk.Label(status_frame, text="🔍 Initializing...", 
                                        font=('SF Pro Display', 12))
            self.status_label.pack(pady=(0, 15))
            
            # Progress bar with smooth animation
            self.progress = ttk.Progressbar(status_frame, mode='indeterminate', length=350)
            self.progress.pack()
            self.progress.start(8)  # Smooth animation
            
            # Footer
            footer_frame = ttk.Frame(main_frame)
            footer_frame.pack(side=tk.BOTTOM, fill=tk.X)
            
            ttk.Label(footer_frame, text="Created by Artur Grochau", 
                     font=('SF Pro Display', 10), foreground='gray').pack()
            
            # Prevent accidental closing during setup
            self.window.protocol("WM_DELETE_WINDOW", self._on_close_attempt)
            
            # Mark as setup complete
            self._setup_complete = True
            
        except Exception as e:
            print(f"⚠️ Could not create splash screen: {e}")
            self.window = None
    
    def _on_close_attempt(self):
        """Handle close attempts gracefully"""
        if not self._setup_complete:
            return  # Don't allow closing during setup
        self.destroy()
    
    def update_status(self, message):
        """Update status safely without modals"""
        if self.window and not self.destroyed and self._setup_complete:
            try:
                if self.window.winfo_exists():
                    self.status_label.config(text=message)
                    self.window.update_idletasks()
            except (tk.TclError, AttributeError):
                pass
        
        # Always print to console as fallback
        print(message)
    
    def pump_events(self):
        """Pump events without blocking"""
        if self.window and not self.destroyed and self._setup_complete:
            try:
                if self.window.winfo_exists():
                    self.window.update_idletasks()
                    return True
            except (tk.TclError, AttributeError):
                pass
        return False
    
    def destroy(self):
        """Safely destroy splash screen"""
        if self.window and not self.destroyed:
            try:
                self.destroyed = True
                if self.window.winfo_exists():
                    self.window.destroy()
            except (tk.TclError, AttributeError):
                pass
        self.window = None

class BundledInstaller:
    """Handles bundled dependencies installation"""
    
    def __init__(self, splash=None):
        self.splash = splash
        self.app_dir = Path(__file__).parent.absolute()
    
    def check_dependencies(self):
        """Check if required dependencies are available"""
        try:
            import click
            return True
        except ImportError:
            return False
    
    def run_bundled_install_script(self):
        """Run the bundled install.sh script"""
        install_script = self.app_dir / "install.sh"
        
        if not install_script.exists():
            self.update_status("❌ install.sh not found in bundle")
            return False
        
        try:
            self.update_status("🔧 Running installation script...")
            
            # Make sure script is executable
            os.chmod(install_script, 0o755)
            
            # Run install script
            result = subprocess.run(
                ["/bin/bash", str(install_script)],
                cwd=self.app_dir,
                capture_output=True,
                text=True,
                timeout=120  # 2 minute timeout
            )
            
            if result.returncode == 0:
                self.update_status("✅ Installation completed!")
                return True
            else:
                self.update_status(f"❌ Installation failed: {result.stderr[:100]}")
                return False
                
        except subprocess.TimeoutExpired:
            self.update_status("❌ Installation timed out")
            return False
        except Exception as e:
            self.update_status(f"❌ Installation error: {str(e)[:50]}")
            return False
    
    def install_pip_packages(self):
        """Fallback: Install packages directly via pip"""
        requirements_file = self.app_dir / "requirements.txt"
        
        if not requirements_file.exists():
            self.update_status("❌ requirements.txt not found")
            return False
        
        try:
            self.update_status("📦 Installing Python packages...")
            
            # Create virtual environment
            venv_dir = self.app_dir / ".venv"
            if not venv_dir.exists():
                subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], 
                              check=True, capture_output=True)
            
            # Find venv python
            venv_python = venv_dir / "bin" / "python3"
            if not venv_python.exists():
                venv_python = venv_dir / "bin" / "python"
            
            if not venv_python.exists():
                self.update_status("❌ Virtual environment setup failed")
                return False
            
            # Install requirements
            subprocess.run([
                str(venv_python), "-m", "pip", "install", 
                "-r", str(requirements_file), "--quiet"
            ], check=True, capture_output=True)
            
            # Update sys.path
            site_packages = list(venv_dir.glob("lib/python*/site-packages"))
            for sp in site_packages:
                sys.path.insert(0, str(sp))
            
            self.update_status("✅ Package installation completed!")
            return True
            
        except Exception as e:
            self.update_status(f"❌ Package installation failed: {str(e)[:50]}")
            return False
    
    def update_status(self, message):
        """Update status through splash screen"""
        if self.splash:
            self.splash.update_status(message)
        else:
            print(message)

class UltimateGUILauncher:
    """Ultimate launcher with perfect OOTB experience"""
    
    def __init__(self):
        self.splash = None
        self.installer = None
    
    def show_final_error(self, title, message):
        """Show final error only if everything else fails"""
        print(f"❌ {title}: {message}")
        
        # Only show GUI error if tkinter is available
        if TKINTER_AVAILABLE:
            try:
                # Create minimal error window
                root = tk.Tk()
                root.withdraw()
                
                error_window = tk.Toplevel(root)
                error_window.title(title)
                error_window.geometry("400x200")
                error_window.resizable(False, False)
                
                # Center window
                error_window.update_idletasks()
                x = (error_window.winfo_screenwidth() // 2) - (200)
                y = (error_window.winfo_screenheight() // 2) - (100)
                error_window.geometry(f"400x200+{x}+{y}")
                
                # Content
                frame = ttk.Frame(error_window, padding="20")
                frame.pack(fill=tk.BOTH, expand=True)
                
                ttk.Label(frame, text="❌", font=('SF Pro Display', 24)).pack()
                ttk.Label(frame, text=title, font=('SF Pro Display', 14, 'bold')).pack(pady=10)
                
                # Scrollable message
                text_widget = tk.Text(frame, wrap=tk.WORD, height=6, font=('SF Pro Display', 10))
                text_widget.pack(fill=tk.BOTH, expand=True, pady=10)
                text_widget.insert('1.0', message)
                text_widget.config(state=tk.DISABLED)
                
                ttk.Button(frame, text="OK", command=error_window.destroy).pack()
                
                error_window.focus_set()
                error_window.wait_window()
                root.destroy()
                
            except Exception:
                pass  # Fallback to console output already done
    
    def launch_main_application(self):
        """Launch the main GUI application"""
        try:
            self.splash.update_status("🚀 Starting application...")
            time.sleep(0.3)  # Brief pause for user feedback
            
            # Import and run the GUI
            from gui.advanced_layout_manager import AdvancedMonitorLayoutManager
            
            # Close splash before launching
            if self.splash:
                self.splash.destroy()
                self.splash = None
            
            # Launch main app
            app = AdvancedMonitorLayoutManager()
            app.run()
            
        except ImportError as e:
            if self.splash:
                self.splash.destroy()
                self.splash = None
            
            self.show_final_error(
                "Application Error",
                f"Failed to load application modules:\n\n{e}\n\n"
                "Please ensure all project files are present."
            )
        except Exception as e:
            if self.splash:
                self.splash.destroy()
                self.splash = None
                
            self.show_final_error(
                "Unexpected Error", 
                f"An unexpected error occurred:\n\n{e}\n\n"
                "Please try restarting the application."
            )
    
    def run(self):
        """Main entry point with perfect UX"""
        print("🖥️  Monitor Layout Manager v1.3.0 - Ultimate OOTB Experience")
        
        # Change to app directory
        app_dir = Path(__file__).parent.absolute()
        os.chdir(app_dir)
        
        # Create non-blocking splash screen
        self.splash = NonBlockingSplash()
        self.splash.create_and_show()
        
        # Create installer
        self.installer = BundledInstaller(self.splash)
        
        # Setup and launch in background thread
        def setup_and_launch():
            """Setup dependencies and launch app"""
            try:
                # Small delay to ensure splash is visible
                time.sleep(0.2)
                
                # Check if dependencies are ready
                if self.installer.check_dependencies():
                    # Dependencies ready, launch directly
                    self.launch_main_application()
                    return
                
                # Need to install dependencies
                self.splash.update_status("🔧 Setting up dependencies...")
                time.sleep(0.5)
                
                # Try bundled install script first
                if self.installer.run_bundled_install_script():
                    if self.installer.check_dependencies():
                        self.launch_main_application()
                        return
                
                # Fallback to pip install
                self.splash.update_status("📦 Trying alternative installation...")
                if self.installer.install_pip_packages():
                    if self.installer.check_dependencies():
                        self.launch_main_application()
                        return
                
                # Installation failed
                if self.splash:
                    self.splash.destroy()
                    self.splash = None
                
                self.show_final_error(
                    "Setup Failed",
                    "Could not install required dependencies.\n\n"
                    "Please check your internet connection and try again.\n\n"
                    "If the problem persists, try running:\n"
                    "pip install -r requirements.txt"
                )
                
            except Exception as e:
                if self.splash:
                    self.splash.destroy()
                    self.splash = None
                
                self.show_final_error(
                    "Setup Error",
                    f"An error occurred during setup:\n\n{e}"
                )
        
        # Start setup in background
        setup_thread = threading.Thread(target=setup_and_launch, daemon=True)
        setup_thread.start()
        
        # Keep splash alive and pump events
        if self.splash and self.splash.window:
            try:
                while self.splash.pump_events():
                    time.sleep(0.05)  # Small delay to prevent CPU spinning
            except (tk.TclError, AttributeError):
                pass

def main():
    """Application entry point"""
    launcher = UltimateGUILauncher()
    launcher.run()

if __name__ == "__main__":
    main()
