# MIT License
# Copyright (c) 2025 Artur Grochau
# 
# This file is part of Monitor Layout Manager.
# See the LICENSE file in the root directory for full license text.

"""
Advanced Layout Manager GUI - Main application window with visual display configuration
Provides intuitive drag-and-drop display arrangement and layout management
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, font
import math
from typing import Dict, List, Optional, Tuple
import json
from datetime import datetime

from core.advanced_display_manager import AdvancedDisplayManager, Display, LayoutProfile

class DraggableDisplay:
    """Represents a draggable display rectangle on the canvas"""
    
    def __init__(self, canvas: tk.Canvas, display: Display, scale: float = 0.1):
        self.canvas = canvas
        self.display = display
        self.scale = scale
        self.rect_id = None
        self.text_id = None
        self.is_dragging = False
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.callbacks = {'position_changed': []}
        
        self.create_visual()
        self.bind_events()
    
    def create_visual(self):
        """Create the visual representation of the display"""
        # Scale dimensions for display
        width = int(self.display.resolution[0] * self.scale)
        height = int(self.display.resolution[1] * self.scale)
        
        # Position on canvas (centered initially)
        canvas_width = self.canvas.winfo_reqwidth() or 800
        canvas_height = self.canvas.winfo_reqheight() or 600
        
        x = (canvas_width - width) // 2 + (self.display.current_position[0] * self.scale)
        y = (canvas_height - height) // 2 - (self.display.current_position[1] * self.scale)  # Invert Y
        
        # Choose colors based on display type and status
        if self.display.type == "macbook":
            fill_color = "#4A90E2"  # Blue for MacBook
            outline_color = "#2E5C8A"
        else:
            fill_color = "#7ED321"  # Green for external displays
            outline_color = "#5AA018"
        
        if self.display.is_main:
            outline_width = 4
            outline_color = "#FF6B35"  # Orange for main display
        else:
            outline_width = 2
        
        # Create rectangle
        self.rect_id = self.canvas.create_rectangle(
            x, y, x + width, y + height,
            fill=fill_color,
            outline=outline_color,
            width=outline_width,
            tags=("display", f"display_{self.display.id}")
        )
        
        # Add display info text
        text_lines = [
            self.display.name,
            f"{self.display.resolution[0]}×{self.display.resolution[1]}",
            f"{self.display.hz}Hz" if self.display.hz else "",
            "Main" if self.display.is_main else ""
        ]
        text_content = "\n".join(line for line in text_lines if line)
        
        self.text_id = self.canvas.create_text(
            x + width // 2, y + height // 2,
            text=text_content,
            font=("Arial", 9, "bold"),
            fill="white",
            anchor="center",
            tags=("display_text", f"text_{self.display.id}")
        )
    
    def bind_events(self):
        """Bind mouse events for dragging"""
        self.canvas.tag_bind(self.rect_id, "<Button-1>", self.on_click)
        self.canvas.tag_bind(self.rect_id, "<B1-Motion>", self.on_drag)
        self.canvas.tag_bind(self.rect_id, "<ButtonRelease-1>", self.on_release)
        self.canvas.tag_bind(self.text_id, "<Button-1>", self.on_click)
        self.canvas.tag_bind(self.text_id, "<B1-Motion>", self.on_drag)
        self.canvas.tag_bind(self.text_id, "<ButtonRelease-1>", self.on_release)
    
    def on_click(self, event):
        """Handle mouse click"""
        self.is_dragging = True
        self.drag_start_x = event.x
        self.drag_start_y = event.y
        # Bring to front
        self.canvas.tag_raise(self.rect_id)
        self.canvas.tag_raise(self.text_id)
    
    def on_drag(self, event):
        """Handle mouse drag"""
        if self.is_dragging:
            dx = event.x - self.drag_start_x
            dy = event.y - self.drag_start_y
            
            # Move both rectangle and text
            self.canvas.move(self.rect_id, dx, dy)
            self.canvas.move(self.text_id, dx, dy)
            
            self.drag_start_x = event.x
            self.drag_start_y = event.y
            
            # Update position
            self._update_position()
    
    def on_release(self, event):
        """Handle mouse release"""
        self.is_dragging = False
        self._notify_position_changed()
    
    def _update_position(self):
        """Update the display position based on canvas position"""
        coords = self.canvas.coords(self.rect_id)
        if coords:
            # Convert canvas coordinates back to display coordinates
            canvas_height = self.canvas.winfo_height()
            x = int(coords[0] / self.scale)
            y = int((canvas_height - coords[3]) / self.scale)  # Invert Y and use bottom of rectangle
            self.display.current_position = (x, y)
    
    def _notify_position_changed(self):
        """Notify callbacks that position changed"""
        for callback in self.callbacks['position_changed']:
            callback(self.display)
    
    def add_callback(self, event_type: str, callback):
        """Add event callback"""
        if event_type in self.callbacks:
            self.callbacks[event_type].append(callback)
    
    def update_visual(self):
        """Update the visual representation"""
        if self.rect_id and self.text_id:
            self.canvas.delete(self.rect_id)
            self.canvas.delete(self.text_id)
        self.create_visual()
        self.bind_events()
    
    def set_position(self, x: int, y: int):
        """Set display position programmatically"""
        # Calculate canvas position
        canvas_height = self.canvas.winfo_height()
        canvas_x = x * self.scale
        canvas_y = canvas_height - (y * self.scale) - (self.display.resolution[1] * self.scale)
        
        # Get current position
        current_coords = self.canvas.coords(self.rect_id)
        if current_coords:
            dx = canvas_x - current_coords[0]
            dy = canvas_y - current_coords[1]
            
            self.canvas.move(self.rect_id, dx, dy)
            self.canvas.move(self.text_id, dx, dy)
        
        self.display.current_position = (x, y)


class DisplayConfigPanel(ttk.Frame):
    """Panel for configuring individual display settings"""
    
    def __init__(self, parent, display: Display, callback=None):
        super().__init__(parent)
        self.display = display
        self.callback = callback
        self.vars = {}
        self.create_widgets()
    
    def create_widgets(self):
        """Create configuration widgets"""
        # Display name
        name_frame = ttk.Frame(self)
        name_frame.pack(fill="x", padx=5, pady=2)
        ttk.Label(name_frame, text=self.display.name, font=("Arial", 10, "bold")).pack(side="left")
        
        if self.display.is_main:
            ttk.Label(name_frame, text="(Main)", foreground="orange").pack(side="right")
        
        # Resolution selection
        res_frame = ttk.Frame(self)
        res_frame.pack(fill="x", padx=5, pady=2)
        ttk.Label(res_frame, text="Resolution:", width=12).pack(side="left")
        
        self.vars['resolution'] = tk.StringVar()
        res_values = [f"{w}×{h}" for w, h in self.display.available_resolutions]
        current_res = f"{self.display.resolution[0]}×{self.display.resolution[1]}"
        self.vars['resolution'].set(current_res)
        
        res_combo = ttk.Combobox(res_frame, textvariable=self.vars['resolution'], 
                                values=res_values, state="readonly", width=12)
        res_combo.pack(side="left", padx=5)
        res_combo.bind("<<ComboboxSelected>>", self._on_change)
        
        # Position (read-only, updated from drag)
        pos_frame = ttk.Frame(self)
        pos_frame.pack(fill="x", padx=5, pady=2)
        ttk.Label(pos_frame, text="Position:", width=12).pack(side="left")
        
        self.vars['position'] = tk.StringVar()
        self.vars['position'].set(f"({self.display.current_position[0]}, {self.display.current_position[1]})")
        ttk.Label(pos_frame, textvariable=self.vars['position'], width=12, relief="sunken").pack(side="left", padx=5)
        
        # Refresh rate
        hz_frame = ttk.Frame(self)
        hz_frame.pack(fill="x", padx=5, pady=2)
        ttk.Label(hz_frame, text="Refresh:", width=12).pack(side="left")
        
        self.vars['hz'] = tk.StringVar()
        hz_values = ["60", "75", "120", "144", "165", "240"]
        self.vars['hz'].set(str(self.display.hz))
        
        hz_combo = ttk.Combobox(hz_frame, textvariable=self.vars['hz'], 
                               values=hz_values, width=8)
        hz_combo.pack(side="left", padx=5)
        hz_combo.bind("<<ComboboxSelected>>", self._on_change)
        
        # Scaling
        scaling_frame = ttk.Frame(self)
        scaling_frame.pack(fill="x", padx=5, pady=2)
        
        self.vars['scaling'] = tk.BooleanVar()
        self.vars['scaling'].set(self.display.scaling)
        ttk.Checkbutton(scaling_frame, text="HiDPI Scaling", 
                       variable=self.vars['scaling'], command=self._on_change).pack(side="left")
        
        # Main display
        main_frame = ttk.Frame(self)
        main_frame.pack(fill="x", padx=5, pady=2)
        
        self.vars['is_main'] = tk.BooleanVar()
        self.vars['is_main'].set(self.display.is_main)
        ttk.Checkbutton(main_frame, text="Main Display", 
                       variable=self.vars['is_main'], command=self._on_change).pack(side="left")
    
    def update_position_display(self, x: int, y: int):
        """Update position display"""
        self.vars['position'].set(f"({x}, {y})")
    
    def _on_change(self, event=None):
        """Handle configuration changes"""
        if self.callback:
            self.callback(self.display, self.get_config())
    
    def get_config(self) -> Dict:
        """Get current configuration"""
        resolution_str = self.vars['resolution'].get()
        if "×" in resolution_str:
            w, h = resolution_str.split("×")
            resolution = (int(w), int(h))
        else:
            resolution = self.display.resolution
        
        return {
            'resolution': resolution,
            'position': self.display.current_position,
            'hz': int(self.vars['hz'].get() or self.display.hz),
            'scaling': self.vars['scaling'].get(),
            'is_main': self.vars['is_main'].get(),
            'rotation': self.display.rotation,
            'color_depth': self.display.color_depth
        }


class AdvancedMonitorLayoutManager:
    """Main application class for the advanced monitor layout manager"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Advanced Monitor Layout Manager")
        self.root.geometry("1200x800")
        
        # Initialize display manager
        self.display_manager = AdvancedDisplayManager()
        
        # UI components
        self.canvas = None
        self.draggable_displays: Dict[str, DraggableDisplay] = {}
        self.config_panels: Dict[str, DisplayConfigPanel] = {}
        self.current_layout_name = tk.StringVar()
        
        self.setup_ui()
        self.refresh_displays()
    
    def setup_ui(self):
        """Setup the user interface"""
        # Configure style for macOS
        style = ttk.Style()
        if "aqua" in style.theme_names():
            style.theme_use("aqua")
        
        # Configure fonts for macOS
        available_fonts = font.families()
        if "SF Pro Text" in available_fonts:
            default_font = ("SF Pro Text", 11)
            small_font = ("SF Pro Text", 9)
        elif "Helvetica Neue" in available_fonts:
            default_font = ("Helvetica Neue", 11)
            small_font = ("Helvetica Neue", 9)
        else:
            default_font = ("Helvetica", 11)
            small_font = ("Helvetica", 9)
        
        # Configure ttk styles with macOS fonts
        style.configure("TLabel", font=default_font)
        style.configure("TButton", font=default_font)
        style.configure("TLabelframe.Label", font=default_font)
        style.configure("Heading.TLabel", font=(default_font[0], default_font[1] + 2, "bold"))
        
        # Store fonts for use in other methods
        self.default_font = default_font
        self.small_font = small_font
        
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Top toolbar
        self.create_toolbar(main_frame)
        
        # Main content area
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill="both", expand=True, pady=(10, 0))
        
        # Left panel - Display list and configurations
        left_frame = ttk.LabelFrame(content_frame, text="Display Configuration", padding=10)
        left_frame.pack(side="left", fill="y", padx=(0, 10))
        left_frame.configure(width=350)
        left_frame.pack_propagate(False)
        
        # Scrollable frame for display configs
        self.create_display_config_area(left_frame)
        
        # Right panel - Visual layout editor
        right_frame = ttk.LabelFrame(content_frame, text="Visual Layout Editor", padding=10)
        right_frame.pack(side="right", fill="both", expand=True)
        
        self.create_visual_editor(right_frame)
        
        # Status bar
        self.create_status_bar(main_frame)
    
    def create_toolbar(self, parent):
        """Create the top toolbar"""
        toolbar = ttk.Frame(parent)
        toolbar.pack(fill="x", pady=(0, 10))
        
        # Left side buttons
        left_buttons = ttk.Frame(toolbar)
        left_buttons.pack(side="left")
        
        ttk.Button(left_buttons, text="🔄 Refresh Displays", 
                  command=self.refresh_displays).pack(side="left", padx=(0, 5))
        
        ttk.Button(left_buttons, text="💾 Save Layout", 
                  command=self.save_current_layout).pack(side="left", padx=5)
        
        ttk.Button(left_buttons, text="📁 Load Layout", 
                  command=self.load_layout_dialog).pack(side="left", padx=5)
        
        ttk.Button(left_buttons, text="🗑️ Delete Layout", 
                  command=self.delete_layout_dialog).pack(side="left", padx=5)
        
        # Center - Current layout name
        center_frame = ttk.Frame(toolbar)
        center_frame.pack(side="left", expand=True, padx=20)
        
        ttk.Label(center_frame, text="Current Layout:").pack(side="left")
        layout_label = ttk.Label(center_frame, textvariable=self.current_layout_name, 
                                font=("Arial", 10, "bold"), foreground="blue")
        layout_label.pack(side="left", padx=(5, 0))
        
        # Right side buttons
        right_buttons = ttk.Frame(toolbar)
        right_buttons.pack(side="right")
        
        ttk.Button(right_buttons, text="✅ Apply Layout", 
                  command=self.apply_current_layout, 
                  style="Accent.TButton").pack(side="left", padx=5)
        
        ttk.Button(right_buttons, text="📤 Export", 
                  command=self.export_layouts).pack(side="left", padx=5)
        
        ttk.Button(right_buttons, text="📥 Import", 
                  command=self.import_layouts).pack(side="left", padx=5)
    
    def create_display_config_area(self, parent):
        """Create the display configuration area"""
        # Create scrollable frame
        canvas = tk.Canvas(parent, bg="white")
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.config_frame = scrollable_frame
        
        # Bind mousewheel to canvas
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind("<MouseWheel>", on_mousewheel)
    
    def create_visual_editor(self, parent):
        """Create the visual layout editor"""
        # Instructions
        instructions = ttk.Label(parent, 
                               text="Drag displays to arrange them. The orange border indicates the main display.",
                               font=("Arial", 9))
        instructions.pack(pady=(0, 10))
        
        # Canvas for display positioning
        canvas_frame = ttk.Frame(parent)
        canvas_frame.pack(fill="both", expand=True)
        
        self.canvas = tk.Canvas(canvas_frame, bg="#F0F0F0", relief="sunken", bd=2)
        self.canvas.pack(fill="both", expand=True)
        
        # Add grid lines for reference
        self.canvas.bind("<Configure>", self.draw_grid)
        
        # Scale controls
        scale_frame = ttk.Frame(parent)
        scale_frame.pack(fill="x", pady=(10, 0))
        
        ttk.Label(scale_frame, text="Scale:").pack(side="left")
        
        self.scale_var = tk.DoubleVar()
        self.scale_var.set(0.1)
        scale_scale = ttk.Scale(scale_frame, from_=0.05, to=0.3, 
                               variable=self.scale_var, orient="horizontal")
        scale_scale.pack(side="left", fill="x", expand=True, padx=5)
        scale_scale.bind("<Motion>", self.on_scale_change)
        
        ttk.Label(scale_frame, text="10%").pack(side="right")
        
        # Preset arrangement buttons
        preset_frame = ttk.Frame(parent)
        preset_frame.pack(fill="x", pady=(10, 0))
        
        ttk.Button(preset_frame, text="📐 Auto Arrange", 
                  command=self.auto_arrange_displays).pack(side="left", padx=(0, 5))
        
        ttk.Button(preset_frame, text="📏 Align Horizontally", 
                  command=self.align_horizontal).pack(side="left", padx=5)
        
        ttk.Button(preset_frame, text="📐 Align Vertically", 
                  command=self.align_vertical).pack(side="left", padx=5)
    
    def create_status_bar(self, parent):
        """Create the status bar"""
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill="x", side="bottom", pady=(10, 0))
        
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        
        ttk.Label(status_frame, textvariable=self.status_var).pack(side="left")
        
        # Creator attribution in the center
        creator_label = ttk.Label(status_frame, text="Created by Artur Grochau", 
                                font=self.small_font)
        creator_label.pack(side="left", expand=True)
        
        # Display count
        self.display_count_var = tk.StringVar()
        ttk.Label(status_frame, textvariable=self.display_count_var).pack(side="right")
    
    def draw_grid(self, event=None):
        """Draw reference grid on canvas"""
        self.canvas.delete("grid")
        
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        
        grid_size = 50
        
        # Vertical lines
        for x in range(0, width, grid_size):
            self.canvas.create_line(x, 0, x, height, fill="#E0E0E0", tags="grid")
        
        # Horizontal lines
        for y in range(0, height, grid_size):
            self.canvas.create_line(0, y, width, y, fill="#E0E0E0", tags="grid")
    
    def refresh_displays(self):
        """Refresh connected displays"""
        self.status_var.set("Detecting displays...")
        self.root.update()
        
        displays = self.display_manager.detect_displays()
        
        if displays:
            self.update_display_configs(displays)
            self.update_visual_editor(displays)
            self.display_count_var.set(f"{len(displays)} display(s) detected")
            self.status_var.set("Ready")
        else:
            self.status_var.set("No displays detected")
            messagebox.showwarning("No Displays", "No displays were detected. Make sure displayplacer is installed.")
    
    def update_display_configs(self, displays: Dict[str, Display]):
        """Update display configuration panels"""
        # Clear existing panels
        for widget in self.config_frame.winfo_children():
            widget.destroy()
        
        self.config_panels.clear()
        
        # Create new panels
        for display_id, display in displays.items():
            panel = DisplayConfigPanel(self.config_frame, display, self.on_display_config_change)
            panel.pack(fill="x", pady=5)
            self.config_panels[display_id] = panel
            
            # Add separator
            if len(self.config_panels) < len(displays):
                ttk.Separator(self.config_frame, orient="horizontal").pack(fill="x", pady=10)
    
    def update_visual_editor(self, displays: Dict[str, Display]):
        """Update visual editor with displays"""
        # Clear existing displays
        self.canvas.delete("display")
        self.canvas.delete("display_text")
        self.draggable_displays.clear()
        
        # Create new draggable displays
        for display_id, display in displays.items():
            draggable = DraggableDisplay(self.canvas, display, self.scale_var.get())
            draggable.add_callback('position_changed', self.on_display_position_changed)
            self.draggable_displays[display_id] = draggable
        
        # Redraw grid on top
        self.draw_grid()
    
    def on_display_config_change(self, display: Display, config: Dict):
        """Handle display configuration changes"""
        # Update display object
        display.resolution = config['resolution']
        display.hz = config['hz']
        display.scaling = config['scaling']
        display.is_main = config['is_main']
        display.rotation = config['rotation']
        display.color_depth = config['color_depth']
        
        # Update visual representation
        if display.id in self.draggable_displays:
            self.draggable_displays[display.id].update_visual()
        
        self.status_var.set("Configuration updated")
    
    def on_display_position_changed(self, display: Display):
        """Handle display position changes"""
        # Update position in config panel
        if display.id in self.config_panels:
            x, y = display.current_position
            self.config_panels[display.id].update_position_display(x, y)
        
        self.status_var.set(f"Moved {display.name} to {display.current_position}")
    
    def on_scale_change(self, event=None):
        """Handle scale changes"""
        new_scale = self.scale_var.get()
        
        for draggable in self.draggable_displays.values():
            draggable.scale = new_scale
            draggable.update_visual()
        
        # Update scale label
        scale_percent = int(new_scale * 100)
        # Find and update the scale label
        for widget in event.widget.master.winfo_children():
            if isinstance(widget, ttk.Label) and widget.cget("text").endswith("%"):
                widget.configure(text=f"{scale_percent}%")
                break
    
    def auto_arrange_displays(self):
        """Automatically arrange displays in a sensible layout"""
        displays = list(self.draggable_displays.values())
        if len(displays) <= 1:
            return
        
        # Find the main display
        main_display = None
        other_displays = []
        
        for draggable in displays:
            if draggable.display.is_main:
                main_display = draggable
            else:
                other_displays.append(draggable)
        
        if not main_display:
            main_display = displays[0]
            other_displays = displays[1:]
        
        # Position main display at origin
        main_display.set_position(0, 0)
        
        # Position other displays to the right
        x_offset = main_display.display.resolution[0]
        
        for i, draggable in enumerate(other_displays):
            draggable.set_position(x_offset, 0)
            x_offset += draggable.display.resolution[0]
        
        self.status_var.set("Displays auto-arranged")
    
    def align_horizontal(self):
        """Align all displays horizontally"""
        if not self.draggable_displays:
            return
        
        # Use the main display's Y position as reference
        main_y = 0
        for draggable in self.draggable_displays.values():
            if draggable.display.is_main:
                main_y = draggable.display.current_position[1]
                break
        
        for draggable in self.draggable_displays.values():
            if not draggable.display.is_main:
                x, _ = draggable.display.current_position
                draggable.set_position(x, main_y)
        
        self.status_var.set("Displays aligned horizontally")
    
    def align_vertical(self):
        """Align all displays vertically"""
        if not self.draggable_displays:
            return
        
        # Use the main display's X position as reference
        main_x = 0
        for draggable in self.draggable_displays.values():
            if draggable.display.is_main:
                main_x = draggable.display.current_position[0]
                break
        
        current_y = 0
        for draggable in self.draggable_displays.values():
            if draggable.display.is_main:
                draggable.set_position(main_x, 0)
            else:
                current_y -= draggable.display.resolution[1]
                draggable.set_position(main_x, current_y)
        
        self.status_var.set("Displays aligned vertically")
    
    def save_current_layout(self):
        """Save current layout"""
        name = simpledialog.askstring("Save Layout", "Enter layout name:")
        if not name:
            return
        
        description = simpledialog.askstring("Save Layout", "Enter description (optional):") or ""
        
        # Collect current configuration
        current_config = {}
        for display_id, panel in self.config_panels.items():
            current_config[display_id] = panel.get_config()
        
        # Update display manager with current positions
        for display_id, draggable in self.draggable_displays.items():
            if display_id in self.display_manager.displays:
                self.display_manager.displays[display_id].current_position = draggable.display.current_position
        
        if self.display_manager.save_layout(name, description):
            self.current_layout_name.set(name)
            self.status_var.set(f"Layout '{name}' saved successfully")
            messagebox.showinfo("Success", f"Layout '{name}' saved successfully!")
        else:
            messagebox.showerror("Error", "Failed to save layout")
    
    def load_layout_dialog(self):
        """Show load layout dialog"""
        layouts = self.display_manager.get_layout_names()
        if not layouts:
            messagebox.showinfo("No Layouts", "No saved layouts found.")
            return
        
        # Create selection dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Load Layout")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Layout list
        list_frame = ttk.Frame(dialog)
        list_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        listbox = tk.Listbox(list_frame)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=listbox.yview)
        listbox.configure(yscrollcommand=scrollbar.set)
        
        for layout_name in layouts:
            listbox.insert(tk.END, layout_name)
        
        listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        def on_load():
            selection = listbox.curselection()
            if selection:
                layout_name = listbox.get(selection[0])
                self.load_layout(layout_name)
                dialog.destroy()
        
        def on_cancel():
            dialog.destroy()
        
        ttk.Button(button_frame, text="Load", command=on_load).pack(side="right", padx=5)
        ttk.Button(button_frame, text="Cancel", command=on_cancel).pack(side="right")
        
        # Center dialog
        dialog.geometry("+%d+%d" % (self.root.winfo_rootx() + 50, self.root.winfo_rooty() + 50))
    
    def load_layout(self, layout_name: str):
        """Load a specific layout"""
        layout = self.display_manager.get_layout(layout_name)
        if not layout:
            messagebox.showerror("Error", f"Layout '{layout_name}' not found")
            return
        
        # Update display positions and configurations
        for display_id, config in layout.displays.items():
            if display_id in self.draggable_displays:
                draggable = self.draggable_displays[display_id]
                
                # Update position
                position = config.get('position', (0, 0))
                draggable.set_position(position[0], position[1])
                
                # Update display properties
                draggable.display.resolution = config.get('resolution', draggable.display.resolution)
                draggable.display.scaling = config.get('scaling', draggable.display.scaling)
                draggable.display.is_main = config.get('is_main', draggable.display.is_main)
                draggable.display.hz = config.get('hz', draggable.display.hz)
                draggable.display.rotation = config.get('rotation', draggable.display.rotation)
                
                # Update visual
                draggable.update_visual()
        
        # Update configuration panels
        for display_id, panel in self.config_panels.items():
            if display_id in layout.displays:
                config = layout.displays[display_id]
                
                # Update UI elements
                if 'resolution' in config:
                    w, h = config['resolution']
                    panel.vars['resolution'].set(f"{w}×{h}")
                if 'hz' in config:
                    panel.vars['hz'].set(str(config['hz']))
                if 'scaling' in config:
                    panel.vars['scaling'].set(config['scaling'])
                if 'is_main' in config:
                    panel.vars['is_main'].set(config['is_main'])
        
        self.current_layout_name.set(layout_name)
        self.status_var.set(f"Layout '{layout_name}' loaded")
    
    def delete_layout_dialog(self):
        """Show delete layout dialog"""
        layouts = self.display_manager.get_layout_names()
        if not layouts:
            messagebox.showinfo("No Layouts", "No saved layouts found.")
            return
        
        # Simple selection dialog
        layout_name = tk.simpledialog.askstring(
            "Delete Layout",
            f"Enter layout name to delete:\nAvailable: {', '.join(layouts)}"
        )
        
        if layout_name and layout_name in layouts:
            if messagebox.askyesno("Confirm Delete", f"Delete layout '{layout_name}'?"):
                if self.display_manager.delete_layout(layout_name):
                    self.status_var.set(f"Layout '{layout_name}' deleted")
                    if self.current_layout_name.get() == layout_name:
                        self.current_layout_name.set("")
                else:
                    messagebox.showerror("Error", "Failed to delete layout")
        elif layout_name:
            messagebox.showerror("Error", f"Layout '{layout_name}' not found")
    
    def apply_current_layout(self):
        """Apply the currently configured layout"""
        if messagebox.askyesno("Apply Layout", "Apply the current display configuration?"):
            # Collect current configuration
            config = {}
            for display_id, panel in self.config_panels.items():
                config[display_id] = panel.get_config()
            
            # Create a temporary layout
            temp_layout_name = f"temp_{int(datetime.now().timestamp())}"
            layout = LayoutProfile(
                name=temp_layout_name,
                description="Temporary layout for applying",
                displays=config,
                created_at=datetime.now().isoformat()
            )
            
            self.display_manager.layouts[temp_layout_name] = layout
            
            if self.display_manager.apply_layout(temp_layout_name):
                self.status_var.set("Layout applied successfully")
                messagebox.showinfo("Success", "Layout applied successfully!")
                # Clean up temporary layout
                del self.display_manager.layouts[temp_layout_name]
            else:
                messagebox.showerror("Error", "Failed to apply layout")
                del self.display_manager.layouts[temp_layout_name]
    
    def export_layouts(self):
        """Export layouts to a file"""
        from tkinter import filedialog
        
        filename = filedialog.asksaveasfilename(
            title="Export Layouts",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                import json
                from dataclasses import asdict
                
                data = {}
                for name, layout in self.display_manager.layouts.items():
                    data[name] = asdict(layout)
                
                with open(filename, 'w') as f:
                    json.dump(data, f, indent=2)
                
                self.status_var.set(f"Layouts exported to {filename}")
                messagebox.showinfo("Success", f"Layouts exported to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export layouts: {e}")
    
    def import_layouts(self):
        """Import layouts from a file"""
        from tkinter import filedialog
        
        filename = filedialog.askopenfilename(
            title="Import Layouts",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                import json
                
                with open(filename, 'r') as f:
                    data = json.load(f)
                
                imported_count = 0
                for name, layout_data in data.items():
                    layout = LayoutProfile(**layout_data)
                    self.display_manager.layouts[name] = layout
                    imported_count += 1
                
                self.display_manager.save_layouts()
                self.status_var.set(f"Imported {imported_count} layout(s)")
                messagebox.showinfo("Success", f"Imported {imported_count} layout(s) from {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to import layouts: {e}")
    
    def run(self):
        """Run the application"""
        self.root.mainloop()


if __name__ == "__main__":
    app = AdvancedMonitorLayoutManager()
    app.run()
