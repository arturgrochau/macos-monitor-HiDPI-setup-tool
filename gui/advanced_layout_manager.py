"""
Advanced Monitor Layout Manager GUI
Tkinter-based interface for managing monitor layouts with drag-and-drop positioning.
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, font
from typing import Dict, List, Optional, Tuple
import json
from datetime import datetime

from core.advanced_display_manager import AdvancedDisplayManager, Display, LayoutProfile
from utils.helpers import is_hidpi_recommended

# Canvas coordinate constants — display (0,0) maps to this canvas position.
# X grows right, Y grows down on canvas but up in display space.
_CANVAS_ORIGIN_X = 100   # px from left edge
_CANVAS_MARGIN_Y = 50    # px from bottom edge to display y=0


def _display_to_canvas(display_x: int, display_y: int, display_h: int,
                       canvas_h: int, scale: float) -> Tuple[float, float]:
    """Convert display origin (bottom-left) → canvas top-left corner of the rect."""
    cx = _CANVAS_ORIGIN_X + display_x * scale
    cy = (canvas_h - _CANVAS_MARGIN_Y) - (display_y + display_h) * scale
    return cx, cy


def _canvas_to_display(rect_x1: float, rect_y2: float,
                       canvas_h: int, scale: float) -> Tuple[int, int]:
    """Convert canvas rect (x1, y2) → display coordinates of that rect's origin."""
    dx = int((rect_x1 - _CANVAS_ORIGIN_X) / scale)
    dy = int(((canvas_h - _CANVAS_MARGIN_Y) - rect_y2) / scale)
    return dx, dy


class DraggableDisplay:
    """Draggable rectangle representing a physical display on the layout canvas."""

    def __init__(self, canvas: tk.Canvas, display: Display, scale: float = 0.1):
        self.canvas = canvas
        self.display = display
        self.scale = scale
        self.rect_id: Optional[int] = None
        self.text_id: Optional[int] = None
        self.is_dragging = False
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.callbacks: Dict[str, list] = {'position_changed': []}

        self.create_visual()
        self.bind_events()

    def _canvas_height(self) -> int:
        h = self.canvas.winfo_height()
        return h if h > 10 else (self.canvas.winfo_reqheight() or 600)

    def create_visual(self):
        """Draw the rectangle and label from current display state."""
        dx, dy = self.display.current_position
        ch = self._canvas_height()
        cx, cy = _display_to_canvas(dx, dy, self.display.resolution[1], ch, self.scale)
        w = int(self.display.resolution[0] * self.scale)
        h = int(self.display.resolution[1] * self.scale)

        # Colours
        if self.display.type == "macbook":
            fill_color = "#4A90E2"
            outline_color = "#2E5C8A"
        else:
            fill_color = "#5BA85A"
            outline_color = "#3D7A3C"

        if self.display.is_main:
            outline_color = "#E8702A"
            outline_width = 4
        else:
            outline_width = 2

        self.rect_id = self.canvas.create_rectangle(
            cx, cy, cx + w, cy + h,
            fill=fill_color, outline=outline_color, width=outline_width,
            tags=("display", f"display_{self.display.id}")
        )

        hidpi_tag = " [HiDPI]" if self.display.scaling else ""
        lines = [
            self.display.name,
            f"{self.display.resolution[0]}×{self.display.resolution[1]}{hidpi_tag}",
            f"{self.display.hz}Hz" if self.display.hz else "",
            "● Main" if self.display.is_main else "",
        ]
        label = "\n".join(l for l in lines if l)

        self.text_id = self.canvas.create_text(
            cx + w // 2, cy + h // 2,
            text=label,
            font=("Arial", 9, "bold"),
            fill="white",
            anchor="center",
            tags=("display_text", f"text_{self.display.id}")
        )

    def bind_events(self):
        for item_id in (self.rect_id, self.text_id):
            self.canvas.tag_bind(item_id, "<Button-1>", self.on_click)
            self.canvas.tag_bind(item_id, "<B1-Motion>", self.on_drag)
            self.canvas.tag_bind(item_id, "<ButtonRelease-1>", self.on_release)

    def on_click(self, event):
        self.is_dragging = True
        self.drag_start_x = event.x
        self.drag_start_y = event.y
        self.canvas.tag_raise(self.rect_id)
        self.canvas.tag_raise(self.text_id)

    def on_drag(self, event):
        if not self.is_dragging:
            return
        dx = event.x - self.drag_start_x
        dy = event.y - self.drag_start_y
        self.canvas.move(self.rect_id, dx, dy)
        self.canvas.move(self.text_id, dx, dy)
        self.drag_start_x = event.x
        self.drag_start_y = event.y
        self._sync_from_canvas()

    def on_release(self, event):
        self.is_dragging = False
        self._sync_from_canvas()
        for cb in self.callbacks['position_changed']:
            cb(self.display)

    def _sync_from_canvas(self):
        """Update display.current_position from the canvas rect's current location."""
        coords = self.canvas.coords(self.rect_id)
        if coords:
            ch = self._canvas_height()
            # coords = [x1, y1, x2, y2]; use x1 and y2 (bottom of rect)
            display_x, display_y = _canvas_to_display(coords[0], coords[3], ch, self.scale)
            self.display.current_position = (display_x, display_y)

    def add_callback(self, event_type: str, callback):
        if event_type in self.callbacks:
            self.callbacks[event_type].append(callback)

    def update_visual(self):
        """Redraw completely from current display state (safe to call on scale/resolution change)."""
        if self.rect_id is not None:
            self.canvas.delete(self.rect_id)
        if self.text_id is not None:
            self.canvas.delete(self.text_id)
        self.create_visual()
        self.bind_events()

    def set_position(self, display_x: int, display_y: int):
        """Move display to given display-space coordinates and redraw."""
        self.display.current_position = (display_x, display_y)
        self.update_visual()


class DisplayConfigPanel(ttk.Frame):
    """Per-display settings panel in the left sidebar."""

    def __init__(self, parent, display: Display, callback=None):
        super().__init__(parent)
        self.display = display
        self.callback = callback
        self.vars: Dict[str, tk.Variable] = {}
        self._hidpi_hint_var = tk.StringVar()
        self.create_widgets()

    def create_widgets(self):
        # Header row
        header = ttk.Frame(self)
        header.pack(fill="x", padx=5, pady=(4, 2))
        ttk.Label(header, text=self.display.name, font=("Arial", 10, "bold")).pack(side="left")
        if self.display.is_main:
            ttk.Label(header, text="Main", foreground="#E8702A").pack(side="right")

        # Resolution
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
        res_combo.bind("<<ComboboxSelected>>", self._on_resolution_change)

        # Position (read-only, driven by drag)
        pos_frame = ttk.Frame(self)
        pos_frame.pack(fill="x", padx=5, pady=2)
        ttk.Label(pos_frame, text="Position:", width=12).pack(side="left")
        self.vars['position'] = tk.StringVar()
        self.vars['position'].set(
            f"({self.display.current_position[0]}, {self.display.current_position[1]})")
        ttk.Label(pos_frame, textvariable=self.vars['position'],
                  width=14, relief="sunken").pack(side="left", padx=5)

        # Refresh rate
        hz_frame = ttk.Frame(self)
        hz_frame.pack(fill="x", padx=5, pady=2)
        ttk.Label(hz_frame, text="Refresh:", width=12).pack(side="left")
        self.vars['hz'] = tk.StringVar(value=str(self.display.hz))
        hz_combo = ttk.Combobox(hz_frame, textvariable=self.vars['hz'],
                                values=["30", "48", "60", "75", "90", "120", "144", "165", "240"],
                                width=8)
        hz_combo.pack(side="left", padx=5)
        hz_combo.bind("<<ComboboxSelected>>", self._on_change)

        # HiDPI scaling with auto-recommendation
        scaling_frame = ttk.Frame(self)
        scaling_frame.pack(fill="x", padx=5, pady=2)
        self.vars['scaling'] = tk.BooleanVar(value=self.display.scaling)
        ttk.Checkbutton(scaling_frame, text="HiDPI Scaling",
                        variable=self.vars['scaling'],
                        command=self._on_change).pack(side="left")
        ttk.Label(scaling_frame, textvariable=self._hidpi_hint_var,
                  foreground="gray", font=("Arial", 8)).pack(side="left", padx=4)
        self._update_hidpi_hint()

        # Main display toggle
        main_frame = ttk.Frame(self)
        main_frame.pack(fill="x", padx=5, pady=(2, 4))
        self.vars['is_main'] = tk.BooleanVar(value=self.display.is_main)
        ttk.Checkbutton(main_frame, text="Set as Main Display",
                        variable=self.vars['is_main'],
                        command=self._on_change).pack(side="left")

    def _update_hidpi_hint(self):
        res_str = self.vars['resolution'].get()
        try:
            w, h = res_str.replace("×", "x").split("x")
            resolution = (int(w), int(h))
        except (ValueError, AttributeError):
            resolution = self.display.resolution
        recommended = is_hidpi_recommended(resolution)
        self._hidpi_hint_var.set("(recommended)" if recommended else "(optional)")

    def _on_resolution_change(self, event=None):
        """On resolution change: auto-suggest HiDPI, then notify parent."""
        res_str = self.vars['resolution'].get()
        try:
            w, h = res_str.replace("×", "x").split("x")
            resolution = (int(w), int(h))
            if is_hidpi_recommended(resolution):
                self.vars['scaling'].set(True)
        except (ValueError, AttributeError):
            pass
        self._update_hidpi_hint()
        self._on_change(event)

    def _on_change(self, event=None):
        if self.callback:
            self.callback(self.display, self.get_config())

    def update_position_display(self, x: int, y: int):
        self.vars['position'].set(f"({x}, {y})")

    def get_config(self) -> Dict:
        res_str = self.vars['resolution'].get()
        try:
            w, h = res_str.replace("×", "x").split("x")
            resolution = (int(w), int(h))
        except (ValueError, AttributeError):
            resolution = self.display.resolution
        return {
            'resolution': resolution,
            'position': self.display.current_position,
            'hz': int(self.vars['hz'].get() or self.display.hz),
            'scaling': self.vars['scaling'].get(),
            'is_main': self.vars['is_main'].get(),
            'rotation': self.display.rotation,
            'color_depth': self.display.color_depth,
        }


class AdvancedMonitorLayoutManager:
    """Main application window."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Monitor Layout Manager")
        self.root.geometry("1200x800")
        self.root.minsize(900, 600)

        self.display_manager = AdvancedDisplayManager()

        self.canvas: Optional[tk.Canvas] = None
        self.draggable_displays: Dict[str, DraggableDisplay] = {}
        self.config_panels: Dict[str, DisplayConfigPanel] = {}
        self.current_layout_name = tk.StringVar()
        self._unsaved_changes = False
        self.scale_label: Optional[ttk.Label] = None

        self._setup_ui()
        self.refresh_displays()

    def _setup_ui(self):
        style = ttk.Style()
        if "aqua" in style.theme_names():
            style.theme_use("aqua")

        available_fonts = font.families()
        if "SF Pro Text" in available_fonts:
            self.default_font = ("SF Pro Text", 11)
            self.small_font = ("SF Pro Text", 9)
        elif "Helvetica Neue" in available_fonts:
            self.default_font = ("Helvetica Neue", 11)
            self.small_font = ("Helvetica Neue", 9)
        else:
            self.default_font = ("Helvetica", 11)
            self.small_font = ("Helvetica", 9)

        style.configure("TLabel", font=self.default_font)
        style.configure("TButton", font=self.default_font)
        style.configure("TLabelframe.Label", font=self.default_font)

        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self._create_toolbar(main_frame)

        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill="both", expand=True, pady=(10, 0))

        left_frame = ttk.LabelFrame(content_frame, text="Display Configuration", padding=10)
        left_frame.pack(side="left", fill="y", padx=(0, 10))
        left_frame.configure(width=340)
        left_frame.pack_propagate(False)
        self._create_display_config_area(left_frame)

        right_frame = ttk.LabelFrame(content_frame, text="Visual Layout Editor", padding=10)
        right_frame.pack(side="right", fill="both", expand=True)
        self._create_visual_editor(right_frame)

        self._create_status_bar(main_frame)

    def _create_toolbar(self, parent):
        toolbar = ttk.Frame(parent)
        toolbar.pack(fill="x", pady=(0, 10))

        left = ttk.Frame(toolbar)
        left.pack(side="left")
        ttk.Button(left, text="Refresh", command=self.refresh_displays).pack(side="left", padx=(0, 5))
        ttk.Button(left, text="Save Layout", command=self.save_current_layout).pack(side="left", padx=5)
        ttk.Button(left, text="Load Layout", command=self.load_layout_dialog).pack(side="left", padx=5)
        ttk.Button(left, text="Delete Layout", command=self.delete_layout_dialog).pack(side="left", padx=5)

        center = ttk.Frame(toolbar)
        center.pack(side="left", expand=True, padx=20)
        ttk.Label(center, text="Current Layout:").pack(side="left")
        self._layout_label = ttk.Label(center, textvariable=self.current_layout_name,
                                       font=("Arial", 10, "bold"), foreground="#2E5C8A")
        self._layout_label.pack(side="left", padx=(5, 0))
        self._unsaved_label = ttk.Label(center, text="", foreground="gray")
        self._unsaved_label.pack(side="left", padx=(3, 0))

        right = ttk.Frame(toolbar)
        right.pack(side="right")
        ttk.Button(right, text="Apply Current Arrangement",
                   command=self.apply_current_layout).pack(side="left", padx=5)
        ttk.Button(right, text="Export", command=self.export_layouts).pack(side="left", padx=5)
        ttk.Button(right, text="Import", command=self.import_layouts).pack(side="left", padx=5)

    def _create_display_config_area(self, parent):
        inner_canvas = tk.Canvas(parent, bg="white")
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=inner_canvas.yview)
        self.config_frame = ttk.Frame(inner_canvas)

        self.config_frame.bind(
            "<Configure>",
            lambda e: inner_canvas.configure(scrollregion=inner_canvas.bbox("all"))
        )
        inner_canvas.create_window((0, 0), window=self.config_frame, anchor="nw")
        inner_canvas.configure(yscrollcommand=scrollbar.set)

        inner_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        inner_canvas.bind("<MouseWheel>",
                          lambda e: inner_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

    def _create_visual_editor(self, parent):
        ttk.Label(parent,
                  text="Drag displays to arrange them.  Orange border = main display.",
                  font=("Arial", 9), foreground="gray").pack(pady=(0, 6))

        self.canvas = tk.Canvas(parent, bg="#F2F2F2", relief="sunken", bd=2)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        # Scale slider
        scale_frame = ttk.Frame(parent)
        scale_frame.pack(fill="x", pady=(8, 0))
        ttk.Label(scale_frame, text="Zoom:").pack(side="left")
        self.scale_var = tk.DoubleVar(value=0.1)
        ttk.Scale(scale_frame, from_=0.03, to=0.4,
                  variable=self.scale_var, orient="horizontal",
                  command=self._on_scale_change).pack(side="left", fill="x", expand=True, padx=5)
        self.scale_label = ttk.Label(scale_frame, text="10%", width=5)
        self.scale_label.pack(side="left")

        # Arrangement helpers
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill="x", pady=(6, 0))
        ttk.Button(btn_frame, text="Auto Arrange",
                   command=self.auto_arrange_displays).pack(side="left", padx=(0, 5))
        ttk.Button(btn_frame, text="Align Horizontal",
                   command=self.align_horizontal).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Align Vertical",
                   command=self.align_vertical).pack(side="left", padx=5)

    def _create_status_bar(self, parent):
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill="x", side="bottom", pady=(8, 0))

        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(status_frame, textvariable=self.status_var).pack(side="left")

        self.display_count_var = tk.StringVar()
        ttk.Label(status_frame, textvariable=self.display_count_var).pack(side="right")

    # ── Canvas helpers ────────────────────────────────────────────────────────

    def _canvas_height(self) -> int:
        h = self.canvas.winfo_height()
        return h if h > 10 else 600

    def draw_grid(self, event=None):
        self.canvas.delete("grid")
        w = self.canvas.winfo_width() or 800
        h = self.canvas.winfo_height() or 600
        for x in range(0, w, 50):
            self.canvas.create_line(x, 0, x, h, fill="#E8E8E8", tags="grid")
        for y in range(0, h, 50):
            self.canvas.create_line(0, y, w, y, fill="#E8E8E8", tags="grid")
        # Re-raise displays above grid
        self.canvas.tag_raise("display")
        self.canvas.tag_raise("display_text")

    def _on_canvas_configure(self, event=None):
        """Redraw grid and all display rects when the canvas is resized."""
        self.draw_grid()
        for d in self.draggable_displays.values():
            d.update_visual()

    def _on_scale_change(self, value=None):
        new_scale = self.scale_var.get()
        for d in self.draggable_displays.values():
            d.scale = new_scale
            d.update_visual()
        self.draw_grid()
        if self.scale_label:
            self.scale_label.configure(text=f"{int(new_scale * 100)}%")

    # ── Display management ───────────────────────────────────────────────────

    def refresh_displays(self):
        self.status_var.set("Detecting displays…")
        self.root.update()
        displays = self.display_manager.detect_displays()
        if not displays:
            self.status_var.set("No displays detected")
            messagebox.showwarning(
                "No Displays Detected",
                "No displays were found.\n\n"
                "Make sure displayplacer is installed:\n"
                "  brew install jakehilborn/jakehilborn/displayplacer\n\n"
                "Then click Refresh."
            )
            return
        self._update_display_configs(displays)
        self._update_visual_editor(displays)
        self.display_count_var.set(f"{len(displays)} display(s)")
        self.status_var.set("Ready")
        self._mark_clean()

    def _update_display_configs(self, displays: Dict[str, Display]):
        for w in self.config_frame.winfo_children():
            w.destroy()
        self.config_panels.clear()

        for i, (display_id, display) in enumerate(displays.items()):
            panel = DisplayConfigPanel(self.config_frame, display,
                                       callback=self.on_display_config_change)
            panel.pack(fill="x", pady=5, padx=4)
            self.config_panels[display_id] = panel
            if i < len(displays) - 1:
                ttk.Separator(self.config_frame, orient="horizontal").pack(fill="x", pady=6)

    def _update_visual_editor(self, displays: Dict[str, Display]):
        self.canvas.delete("display")
        self.canvas.delete("display_text")
        self.draggable_displays.clear()

        for display_id, display in displays.items():
            d = DraggableDisplay(self.canvas, display, self.scale_var.get())
            d.add_callback('position_changed', self.on_display_position_changed)
            self.draggable_displays[display_id] = d

        self.draw_grid()

    def on_display_config_change(self, display: Display, config: Dict):
        """Handle config panel changes — update model and redraw."""
        display.resolution = config['resolution']
        display.hz = config['hz']
        display.scaling = config['scaling']
        display.is_main = config['is_main']
        display.rotation = config['rotation']
        display.color_depth = config['color_depth']

        if display.id in self.draggable_displays:
            self.draggable_displays[display.id].update_visual()

        self.status_var.set("Configuration updated — drag to position, then Save")
        self._mark_dirty()

    def on_display_position_changed(self, display: Display):
        if display.id in self.config_panels:
            x, y = display.current_position
            self.config_panels[display.id].update_position_display(x, y)
        self.status_var.set(f"Moved {display.name} to {display.current_position}")
        self._mark_dirty()

    # ── Dirty / clean state ──────────────────────────────────────────────────

    def _mark_dirty(self):
        if not self._unsaved_changes:
            self._unsaved_changes = True
            self._unsaved_label.configure(text="(unsaved changes)")

    def _mark_clean(self):
        self._unsaved_changes = False
        self._unsaved_label.configure(text="")

    # ── Arrangement helpers ──────────────────────────────────────────────────

    def auto_arrange_displays(self):
        displays = list(self.draggable_displays.values())
        if not displays:
            return
        main = next((d for d in displays if d.display.is_main), displays[0])
        others = [d for d in displays if d is not main]

        main.set_position(0, 0)
        x_offset = main.display.resolution[0]
        for d in others:
            d.set_position(x_offset, 0)
            x_offset += d.display.resolution[0]

        for d in self.draggable_displays.values():
            if d.display.id in self.config_panels:
                x, y = d.display.current_position
                self.config_panels[d.display.id].update_position_display(x, y)

        self.draw_grid()
        self.status_var.set("Auto arranged")
        self._mark_dirty()

    def align_horizontal(self):
        if not self.draggable_displays:
            return
        ref_y = next(
            (d.display.current_position[1] for d in self.draggable_displays.values()
             if d.display.is_main), 0)
        for d in self.draggable_displays.values():
            d.set_position(d.display.current_position[0], ref_y)
        self.draw_grid()
        self.status_var.set("Aligned horizontally")
        self._mark_dirty()

    def align_vertical(self):
        if not self.draggable_displays:
            return
        ref_x = next(
            (d.display.current_position[0] for d in self.draggable_displays.values()
             if d.display.is_main), 0)
        y = 0
        for d in self.draggable_displays.values():
            d.set_position(ref_x, y)
            y -= d.display.resolution[1]
        self.draw_grid()
        self.status_var.set("Aligned vertically")
        self._mark_dirty()

    # ── Layout persistence ───────────────────────────────────────────────────

    def save_current_layout(self):
        # Pre-fill with current name if one is loaded (makes "update" flow obvious)
        pre = self.current_layout_name.get() or ""
        name = simpledialog.askstring("Save Layout", "Layout name:", initialvalue=pre)
        if not name:
            return

        description = simpledialog.askstring(
            "Save Layout", "Description (optional):", initialvalue="") or ""

        # Sync positions from canvas panels into the display manager
        for display_id, draggable in self.draggable_displays.items():
            if display_id in self.display_manager.displays:
                self.display_manager.displays[display_id].current_position = \
                    draggable.display.current_position

        if self.display_manager.save_layout(name, description):
            self.current_layout_name.set(name)
            self._mark_clean()
            self.status_var.set(f"Layout '{name}' saved")
        else:
            messagebox.showerror("Save Failed",
                                 "Could not save the layout. Make sure displayplacer is installed.")

    def load_layout_dialog(self):
        layouts = self.display_manager.get_layout_names()
        if not layouts:
            messagebox.showinfo("No Layouts", "No saved layouts found.")
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Load Layout")
        dialog.geometry("380x280")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.geometry("+%d+%d" % (self.root.winfo_rootx() + 60, self.root.winfo_rooty() + 60))

        list_frame = ttk.Frame(dialog)
        list_frame.pack(fill="both", expand=True, padx=10, pady=10)

        listbox = tk.Listbox(list_frame, activestyle="dotbox")
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=listbox.yview)
        listbox.configure(yscrollcommand=scrollbar.set)

        for layout_name in layouts:
            listbox.insert(tk.END, layout_name)
        if layouts:
            listbox.selection_set(0)

        listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill="x", padx=10, pady=10)

        def on_load():
            sel = listbox.curselection()
            if sel:
                self.load_layout(listbox.get(sel[0]))
                dialog.destroy()

        listbox.bind("<Double-Button-1>", lambda e: on_load())
        ttk.Button(btn_frame, text="Load", command=on_load).pack(side="right", padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side="right")

    def load_layout(self, layout_name: str):
        layout = self.display_manager.get_layout(layout_name)
        if not layout:
            messagebox.showerror("Error", f"Layout '{layout_name}' not found")
            return

        for display_id, config in layout.displays.items():
            if display_id not in self.draggable_displays:
                continue
            draggable = self.draggable_displays[display_id]
            position = config.get('position', (0, 0))
            # Update the display model
            draggable.display.resolution = tuple(config.get('resolution', draggable.display.resolution))
            draggable.display.scaling = config.get('scaling', draggable.display.scaling)
            draggable.display.is_main = config.get('is_main', draggable.display.is_main)
            draggable.display.hz = config.get('hz', draggable.display.hz)
            draggable.display.rotation = config.get('rotation', draggable.display.rotation)
            draggable.set_position(position[0], position[1])

        # Sync config panels
        for display_id, panel in self.config_panels.items():
            if display_id not in layout.displays:
                continue
            config = layout.displays[display_id]
            if 'resolution' in config:
                w, h = config['resolution']
                panel.vars['resolution'].set(f"{w}×{h}")
                panel._update_hidpi_hint()
            if 'hz' in config:
                panel.vars['hz'].set(str(config['hz']))
            if 'scaling' in config:
                panel.vars['scaling'].set(config['scaling'])
            if 'is_main' in config:
                panel.vars['is_main'].set(config['is_main'])
            if 'position' in config:
                panel.update_position_display(*config['position'])

        self.current_layout_name.set(layout_name)
        self._mark_clean()
        self.status_var.set(f"Layout '{layout_name}' loaded")

    def delete_layout_dialog(self):
        layouts = self.display_manager.get_layout_names()
        if not layouts:
            messagebox.showinfo("No Layouts", "No saved layouts found.")
            return

        layout_name = simpledialog.askstring(
            "Delete Layout",
            f"Layout to delete:\n({', '.join(layouts)})"
        )
        if not layout_name:
            return
        if layout_name not in layouts:
            messagebox.showerror("Not Found", f"Layout '{layout_name}' not found")
            return
        if messagebox.askyesno("Confirm Delete", f"Delete layout '{layout_name}'?"):
            self.display_manager.delete_layout(layout_name)
            if self.current_layout_name.get() == layout_name:
                self.current_layout_name.set("")
                self._mark_clean()
            self.status_var.set(f"Layout '{layout_name}' deleted")

    def apply_current_layout(self):
        """Apply the canvas arrangement to the physical displays immediately."""
        if not messagebox.askyesno("Apply Arrangement",
                                   "Apply the current display arrangement now?\n"
                                   "Your monitors will rearrange."):
            return

        config: Dict[str, Dict] = {}
        for display_id, panel in self.config_panels.items():
            cfg = panel.get_config()
            if display_id in self.draggable_displays:
                cfg['position'] = self.draggable_displays[display_id].display.current_position
            config[display_id] = cfg

        temp_name = f"_apply_{int(datetime.now().timestamp())}"
        layout = LayoutProfile(
            name=temp_name,
            description="",
            displays=config,
            created_at=datetime.now().isoformat()
        )
        self.display_manager.layouts[temp_name] = layout

        success = self.display_manager.apply_layout(temp_name)
        del self.display_manager.layouts[temp_name]

        if success:
            self.status_var.set("Arrangement applied")
        else:
            messagebox.showerror("Apply Failed",
                                 "Could not apply the arrangement.\n"
                                 "Run the CLI doctor command for diagnostics:\n"
                                 "  python main.py --cli doctor")

    def export_layouts(self):
        from tkinter import filedialog
        from dataclasses import asdict

        filename = filedialog.asksaveasfilename(
            title="Export Layouts",
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("All files", "*.*")]
        )
        if not filename:
            return
        try:
            data = {n: asdict(l) for n, l in self.display_manager.layouts.items()}
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            self.status_var.set(f"Exported to {filename}")
        except Exception as e:
            messagebox.showerror("Export Failed", str(e))

    def import_layouts(self):
        from tkinter import filedialog

        filename = filedialog.askopenfilename(
            title="Import Layouts",
            filetypes=[("JSON", "*.json"), ("All files", "*.*")]
        )
        if not filename:
            return
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            count = 0
            for name, layout_data in data.items():
                self.display_manager.layouts[name] = LayoutProfile(**layout_data)
                count += 1
            self.display_manager.save_layouts()
            self.status_var.set(f"Imported {count} layout(s)")
        except Exception as e:
            messagebox.showerror("Import Failed", str(e))

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = AdvancedMonitorLayoutManager()
    app.run()
