"""
Settings Dialog for Monitor Layout Manager
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os

class SettingsDialog:
    """Settings configuration dialog"""
    
    def __init__(self, parent):
        self.parent = parent
        self.settings = self.load_settings()
        
        # Create dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Settings")
        self.dialog.geometry("500x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog
        self.dialog.geometry("+%d+%d" % (
            parent.winfo_rootx() + (parent.winfo_width() // 2) - 250,
            parent.winfo_rooty() + (parent.winfo_height() // 2) - 200
        ))
        
        self.create_widgets()
    
    def load_settings(self) -> dict:
        """Load settings from file"""
        settings_file = os.path.expanduser("~/.monitor_layout_settings.json")
        default_settings = {
            "displayplacer_path": "/opt/homebrew/bin/displayplacer",
            "auto_refresh": True,
            "show_grid": True,
            "grid_size": 50,
            "default_scale": 0.1,
            "animation_enabled": True,
            "save_window_position": True,
            "confirmation_dialogs": True,
            "theme": "system"
        }
        
        if os.path.exists(settings_file):
            try:
                with open(settings_file, 'r') as f:
                    saved_settings = json.load(f)
                    default_settings.update(saved_settings)
            except Exception as e:
                print(f"Error loading settings: {e}")
        
        return default_settings
    
    def save_settings(self):
        """Save settings to file"""
        settings_file = os.path.expanduser("~/.monitor_layout_settings.json")
        try:
            with open(settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}")
            return False
    
    def create_widgets(self):
        """Create settings widgets"""
        notebook = ttk.Notebook(self.dialog)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # General settings tab
        general_frame = ttk.Frame(notebook)
        notebook.add(general_frame, text="General")
        self.create_general_settings(general_frame)
        
        # Display settings tab
        display_frame = ttk.Frame(notebook)
        notebook.add(display_frame, text="Display")
        self.create_display_settings(display_frame)
        
        # Advanced settings tab
        advanced_frame = ttk.Frame(notebook)
        notebook.add(advanced_frame, text="Advanced")
        self.create_advanced_settings(advanced_frame)
        
        # Buttons
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Button(button_frame, text="Reset to Defaults", 
                  command=self.reset_defaults).pack(side="left")
        
        ttk.Button(button_frame, text="Cancel", 
                  command=self.on_cancel).pack(side="right", padx=5)
        
        ttk.Button(button_frame, text="Apply", 
                  command=self.on_apply).pack(side="right")
    
    def create_general_settings(self, parent):
        """Create general settings"""
        # DisplayPlacer path
        path_frame = ttk.LabelFrame(parent, text="DisplayPlacer Configuration", padding=10)
        path_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Label(path_frame, text="DisplayPlacer Path:").pack(anchor="w")
        
        path_entry_frame = ttk.Frame(path_frame)
        path_entry_frame.pack(fill="x", pady=(5, 0))
        
        self.path_var = tk.StringVar(value=self.settings["displayplacer_path"])
        path_entry = ttk.Entry(path_entry_frame, textvariable=self.path_var)
        path_entry.pack(side="left", fill="x", expand=True)
        
        ttk.Button(path_entry_frame, text="Browse", 
                  command=self.browse_displayplacer).pack(side="right", padx=(5, 0))
        
        # Auto refresh
        auto_frame = ttk.LabelFrame(parent, text="Display Detection", padding=10)
        auto_frame.pack(fill="x", padx=10, pady=10)
        
        self.auto_refresh_var = tk.BooleanVar(value=self.settings["auto_refresh"])
        ttk.Checkbutton(auto_frame, text="Automatically refresh displays on startup", 
                       variable=self.auto_refresh_var).pack(anchor="w")
        
        # Confirmation dialogs
        confirm_frame = ttk.LabelFrame(parent, text="User Interface", padding=10)
        confirm_frame.pack(fill="x", padx=10, pady=10)
        
        self.confirmation_var = tk.BooleanVar(value=self.settings["confirmation_dialogs"])
        ttk.Checkbutton(confirm_frame, text="Show confirmation dialogs", 
                       variable=self.confirmation_var).pack(anchor="w")
        
        self.save_window_var = tk.BooleanVar(value=self.settings["save_window_position"])
        ttk.Checkbutton(confirm_frame, text="Remember window position and size", 
                       variable=self.save_window_var).pack(anchor="w")
    
    def create_display_settings(self, parent):
        """Create display settings"""
        # Grid settings
        grid_frame = ttk.LabelFrame(parent, text="Grid Settings", padding=10)
        grid_frame.pack(fill="x", padx=10, pady=10)
        
        self.show_grid_var = tk.BooleanVar(value=self.settings["show_grid"])
        ttk.Checkbutton(grid_frame, text="Show reference grid", 
                       variable=self.show_grid_var).pack(anchor="w")
        
        # Grid size
        size_frame = ttk.Frame(grid_frame)
        size_frame.pack(fill="x", pady=(10, 0))
        
        ttk.Label(size_frame, text="Grid Size:").pack(side="left")
        
        self.grid_size_var = tk.IntVar(value=self.settings["grid_size"])
        grid_size_scale = ttk.Scale(size_frame, from_=20, to=100, 
                                   variable=self.grid_size_var, orient="horizontal")
        grid_size_scale.pack(side="left", fill="x", expand=True, padx=10)
        
        grid_size_label = ttk.Label(size_frame, text=f"{self.settings['grid_size']}px")
        grid_size_label.pack(side="right")
        
        def update_grid_label(*args):
            grid_size_label.config(text=f"{int(self.grid_size_var.get())}px")
        
        self.grid_size_var.trace("w", update_grid_label)
        
        # Scale settings
        scale_frame = ttk.LabelFrame(parent, text="Scale Settings", padding=10)
        scale_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Label(scale_frame, text="Default Scale:").pack(anchor="w")
        
        scale_control_frame = ttk.Frame(scale_frame)
        scale_control_frame.pack(fill="x", pady=(5, 0))
        
        self.scale_var = tk.DoubleVar(value=self.settings["default_scale"])
        scale_scale = ttk.Scale(scale_control_frame, from_=0.05, to=0.5, 
                               variable=self.scale_var, orient="horizontal")
        scale_scale.pack(side="left", fill="x", expand=True)
        
        scale_label = ttk.Label(scale_control_frame, text=f"{int(self.settings['default_scale'] * 100)}%")
        scale_label.pack(side="right", padx=(10, 0))
        
        def update_scale_label(*args):
            scale_label.config(text=f"{int(self.scale_var.get() * 100)}%")
        
        self.scale_var.trace("w", update_scale_label)
        
        # Animation
        animation_frame = ttk.LabelFrame(parent, text="Animation", padding=10)
        animation_frame.pack(fill="x", padx=10, pady=10)
        
        self.animation_var = tk.BooleanVar(value=self.settings["animation_enabled"])
        ttk.Checkbutton(animation_frame, text="Enable smooth animations", 
                       variable=self.animation_var).pack(anchor="w")
    
    def create_advanced_settings(self, parent):
        """Create advanced settings"""
        # Theme selection
        theme_frame = ttk.LabelFrame(parent, text="Appearance", padding=10)
        theme_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Label(theme_frame, text="Theme:").pack(anchor="w")
        
        self.theme_var = tk.StringVar(value=self.settings["theme"])
        theme_combo = ttk.Combobox(theme_frame, textvariable=self.theme_var,
                                  values=["system", "light", "dark"], state="readonly")
        theme_combo.pack(fill="x", pady=(5, 0))
        
        # Backup and restore
        backup_frame = ttk.LabelFrame(parent, text="Backup & Restore", padding=10)
        backup_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Button(backup_frame, text="Backup All Layouts", 
                  command=self.backup_layouts).pack(fill="x", pady=2)
        
        ttk.Button(backup_frame, text="Restore Layouts", 
                  command=self.restore_layouts).pack(fill="x", pady=2)
        
        # Reset
        reset_frame = ttk.LabelFrame(parent, text="Reset", padding=10)
        reset_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Button(reset_frame, text="Clear All Saved Layouts", 
                  command=self.clear_layouts,
                  style="Warning.TButton").pack(fill="x", pady=2)
    
    def browse_displayplacer(self):
        """Browse for displayplacer executable"""
        filename = filedialog.askopenfilename(
            title="Select DisplayPlacer Executable",
            initialdir="/opt/homebrew/bin",
            filetypes=[("Executable files", "*"), ("All files", "*.*")]
        )
        
        if filename:
            self.path_var.set(filename)
    
    def backup_layouts(self):
        """Backup all layouts"""
        filename = filedialog.asksaveasfilename(
            title="Backup Layouts",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfilename=f"monitor_layouts_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        
        if filename:
            try:
                # This would need to be connected to the main application
                messagebox.showinfo("Info", "This feature needs to be connected to the main application.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to backup layouts: {e}")
    
    def restore_layouts(self):
        """Restore layouts from backup"""
        filename = filedialog.askopenfilename(
            title="Restore Layouts",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                # This would need to be connected to the main application
                messagebox.showinfo("Info", "This feature needs to be connected to the main application.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to restore layouts: {e}")
    
    def clear_layouts(self):
        """Clear all saved layouts"""
        if messagebox.askyesno("Confirm Clear", 
                              "Are you sure you want to delete ALL saved layouts?\nThis cannot be undone."):
            try:
                # This would need to be connected to the main application
                messagebox.showinfo("Info", "This feature needs to be connected to the main application.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to clear layouts: {e}")
    
    def reset_defaults(self):
        """Reset all settings to defaults"""
        if messagebox.askyesno("Reset Settings", "Reset all settings to default values?"):
            self.settings = {
                "displayplacer_path": "/opt/homebrew/bin/displayplacer",
                "auto_refresh": True,
                "show_grid": True,
                "grid_size": 50,
                "default_scale": 0.1,
                "animation_enabled": True,
                "save_window_position": True,
                "confirmation_dialogs": True,
                "theme": "system"
            }
            
            # Update UI
            self.path_var.set(self.settings["displayplacer_path"])
            self.auto_refresh_var.set(self.settings["auto_refresh"])
            self.show_grid_var.set(self.settings["show_grid"])
            self.grid_size_var.set(self.settings["grid_size"])
            self.scale_var.set(self.settings["default_scale"])
            self.animation_var.set(self.settings["animation_enabled"])
            self.save_window_var.set(self.settings["save_window_position"])
            self.confirmation_var.set(self.settings["confirmation_dialogs"])
            self.theme_var.set(self.settings["theme"])
    
    def on_apply(self):
        """Apply settings"""
        # Update settings from UI
        self.settings["displayplacer_path"] = self.path_var.get()
        self.settings["auto_refresh"] = self.auto_refresh_var.get()
        self.settings["show_grid"] = self.show_grid_var.get()
        self.settings["grid_size"] = int(self.grid_size_var.get())
        self.settings["default_scale"] = self.scale_var.get()
        self.settings["animation_enabled"] = self.animation_var.get()
        self.settings["save_window_position"] = self.save_window_var.get()
        self.settings["confirmation_dialogs"] = self.confirmation_var.get()
        self.settings["theme"] = self.theme_var.get()
        
        if self.save_settings():
            messagebox.showinfo("Success", "Settings saved successfully!")
            self.dialog.destroy()
    
    def on_cancel(self):
        """Cancel settings dialog"""
        self.dialog.destroy()


def show_settings_dialog(parent):
    """Show settings dialog"""
    dialog = SettingsDialog(parent)
    return dialog.settings
