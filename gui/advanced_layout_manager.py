"""
Advanced Monitor Layout Manager GUI
Tkinter-based interface for managing monitor layouts with drag-and-drop positioning.

Coordinate model: display positions are displayplacer/CoreGraphics coordinates
((0,0) = main display's top-left, y grows DOWN). The canvas renders that space
directly (scale + centering offset, no axis flip), so the editor matches both
System Settings and what `displayplacer` will actually apply.
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, font
from typing import Dict, Optional
import json

from core.advanced_display_manager import AdvancedDisplayManager, Display, LayoutProfile
from utils.helpers import is_hidpi_recommended
from gui.canvas_math import (
    Rect,
    clamp_to_view,
    display_to_canvas,
    fit_offset,
    is_contiguous,
    overlaps,
    snap_position,
)

_SNAP_CANVAS_PX = 12          # snap radius, in canvas pixels
_MIN_VISIBLE_PX = 40          # how much of a dragged rect must stay in view


class DraggableDisplay:
    """Draggable rectangle representing a physical display on the layout canvas.

    The Display model is the single source of truth; the canvas items are a
    projection of it. Dragging updates the model (with snapping) and re-renders.
    """

    def __init__(self, canvas: tk.Canvas, display: Display, view):
        self.canvas = canvas
        self.display = display
        self.view = view                     # owner exposing .scale/.offset/.snap_rects
        self.rect_id: Optional[int] = None
        self.text_id: Optional[int] = None
        self.is_dragging = False
        self._grab_dx = 0.0                  # pointer offset inside the rect (canvas px)
        self._grab_dy = 0.0
        self._drag_started_at: Optional[tuple] = None
        self.callbacks: Dict[str, list] = {'position_changed': [], 'drag_finished': []}

        self.create_visual()
        self.bind_events()

    # ── Rendering ────────────────────────────────────────────────────────────

    def _canvas_rect(self):
        dx, dy = self.display.current_position
        cx, cy = display_to_canvas(dx, dy, self.view.offset, self.view.scale)
        w = self.display.resolution[0] * self.view.scale
        h = self.display.resolution[1] * self.view.scale
        return cx, cy, w, h

    def _label(self, rect_w: float) -> str:
        if rect_w < 70:      # tiny rect: name only, keep clicks on the right display
            return self.display.name.split(" (")[0]
        hidpi_tag = " [HiDPI]" if self.display.scaling else ""
        lines = [
            self.display.name,
            f"{self.display.resolution[0]}×{self.display.resolution[1]}{hidpi_tag}",
            f"{self.display.hz}Hz" if self.display.hz else "",
            "● Main" if self.display.is_main else "",
        ]
        return "\n".join(l for l in lines if l)

    def create_visual(self):
        cx, cy, w, h = self._canvas_rect()

        if self.display.type == "macbook":
            fill_color, outline_color = "#4A90E2", "#2E5C8A"
        else:
            fill_color, outline_color = "#5BA85A", "#3D7A3C"
        if self.display.is_main:
            outline_color, outline_width = "#E8702A", 4
        else:
            outline_width = 2

        self.rect_id = self.canvas.create_rectangle(
            cx, cy, cx + w, cy + h,
            fill=fill_color, outline=outline_color, width=outline_width,
            tags=("display", f"display_{self.display.id}")
        )
        self.text_id = self.canvas.create_text(
            cx + w / 2, cy + h / 2,
            text=self._label(w),
            font=("Arial", 9, "bold"),
            fill="white",
            anchor="center",
            width=max(w - 8, 40),
            tags=("display_text", f"text_{self.display.id}")
        )

    def redraw(self):
        """Re-project the model onto the existing canvas items (no re-create)."""
        if self.rect_id is None:
            return
        cx, cy, w, h = self._canvas_rect()
        self.canvas.coords(self.rect_id, cx, cy, cx + w, cy + h)
        self.canvas.coords(self.text_id, cx + w / 2, cy + h / 2)
        self.canvas.itemconfigure(self.text_id, text=self._label(w),
                                  width=max(w - 8, 40))

    def bind_events(self):
        for item_id in (self.rect_id, self.text_id):
            self.canvas.tag_bind(item_id, "<Button-1>", self.on_click)
            self.canvas.tag_bind(item_id, "<B1-Motion>", self.on_drag)
            self.canvas.tag_bind(item_id, "<ButtonRelease-1>", self.on_release)

    def update_visual(self):
        """Full re-create (needed after color/main-outline changes)."""
        if self.rect_id is not None:
            self.canvas.delete(self.rect_id)
        if self.text_id is not None:
            self.canvas.delete(self.text_id)
        self.create_visual()
        self.bind_events()

    # ── Dragging ─────────────────────────────────────────────────────────────

    def on_click(self, event):
        cx, cy, _, _ = self._canvas_rect()
        self.is_dragging = True
        self._grab_dx = event.x - cx
        self._grab_dy = event.y - cy
        self._drag_started_at = self.display.current_position
        self.canvas.tag_raise(self.rect_id)
        self.canvas.tag_raise(self.text_id)

    def on_drag(self, event):
        if not self.is_dragging:
            return
        scale = self.view.scale
        w = self.display.resolution[0] * scale
        h = self.display.resolution[1] * scale

        # Proposed top-left in canvas space, clamped so the rect can't escape view
        cx = event.x - self._grab_dx
        cy = event.y - self._grab_dy
        cx, cy = clamp_to_view(cx, cy, w, h,
                               self.canvas.winfo_width(), self.canvas.winfo_height(),
                               margin=_MIN_VISIBLE_PX)

        # Back to display space, then snap against the stationary displays
        dx = (cx - self.view.offset[0]) / scale
        dy = (cy - self.view.offset[1]) / scale
        moving = Rect(round(dx), round(dy),
                      self.display.resolution[0], self.display.resolution[1])
        others = self.view.snap_rects(exclude_id=self.display.id)
        sx, sy = snap_position(moving, others, threshold=_SNAP_CANVAS_PX / scale)

        if (sx, sy) != self.display.current_position:
            self.display.current_position = (sx, sy)
            self.redraw()
            for cb in self.callbacks['position_changed']:
                cb(self.display)

    def on_release(self, event):
        if not self.is_dragging:
            return
        self.is_dragging = False
        moved = self.display.current_position != self._drag_started_at
        self._drag_started_at = None
        for cb in self.callbacks['drag_finished']:
            cb(self.display, moved)

    def add_callback(self, event_type: str, callback):
        if event_type in self.callbacks:
            self.callbacks[event_type].append(callback)

    def set_position(self, display_x: int, display_y: int):
        self.display.current_position = (display_x, display_y)
        self.redraw()


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

    def _parsed_resolution(self):
        res_str = self.vars['resolution'].get()
        try:
            w, h = res_str.replace("×", "x").split("x")
            return (int(w), int(h))
        except (ValueError, AttributeError):
            return self.display.resolution

    def _update_hidpi_hint(self):
        recommended = is_hidpi_recommended(self._parsed_resolution())
        self._hidpi_hint_var.set("(recommended)" if recommended else "(optional)")

    def _on_resolution_change(self, event=None):
        """On resolution change: auto-suggest HiDPI, then notify parent."""
        if is_hidpi_recommended(self._parsed_resolution()):
            self.vars['scaling'].set(True)
        self._update_hidpi_hint()
        self._on_change(event)

    def _on_change(self, event=None):
        if self.callback:
            self.callback(self.display, self.get_config())

    def update_position_display(self, x: int, y: int):
        self.vars['position'].set(f"({x}, {y})")

    def set_main_checkbox(self, value: bool):
        self.vars['is_main'].set(value)

    def get_config(self) -> Dict:
        try:
            hz = int(self.vars['hz'].get())
            if not (1 <= hz <= 1000):
                raise ValueError
        except (ValueError, tk.TclError):
            hz = self.display.hz
            self.vars['hz'].set(str(hz))
        return {
            'resolution': self._parsed_resolution(),
            'position': self.display.current_position,
            'hz': hz,
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

        # View transform: canvas = display * scale + offset
        self.scale = 0.1
        self.offset = (0.0, 0.0)

        self._setup_ui()
        self.refresh_displays(confirm_discard=False)

    # ── View-state protocol used by DraggableDisplay ─────────────────────────

    def snap_rects(self, exclude_id: str):
        return [
            Rect(d.display.current_position[0], d.display.current_position[1],
                 d.display.resolution[0], d.display.resolution[1])
            for d in self.draggable_displays.values()
            if d.display.id != exclude_id
        ]

    def _all_rects(self):
        return [
            Rect(d.display.current_position[0], d.display.current_position[1],
                 d.display.resolution[0], d.display.resolution[1])
            for d in self.draggable_displays.values()
        ]

    def _any_drag_active(self) -> bool:
        return any(d.is_dragging for d in self.draggable_displays.values())

    def _refit_view(self):
        """Recenter the arrangement in the canvas at the current scale."""
        w = self.canvas.winfo_width() or 800
        h = self.canvas.winfo_height() or 600
        self.offset = fit_offset(self._all_rects(), w, h, self.scale)

    def _redraw_all(self):
        for d in self.draggable_displays.values():
            d.redraw()

    # ── UI setup ─────────────────────────────────────────────────────────────

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

        # macOS delivers small delta values (not Windows' ±120 steps)
        inner_canvas.bind("<MouseWheel>",
                          lambda e: inner_canvas.yview_scroll(-1 if e.delta > 0 else 1, "units"))

    def _create_visual_editor(self, parent):
        ttk.Label(parent,
                  text="Drag displays to arrange them — edges snap together.  Orange border = main display.",
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
        ttk.Button(btn_frame, text="Align Row",
                   command=self.align_horizontal).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Stack Column",
                   command=self.align_vertical).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Center View",
                   command=self._recenter).pack(side="left", padx=5)

    def _create_status_bar(self, parent):
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill="x", side="bottom", pady=(8, 0))

        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(status_frame, textvariable=self.status_var).pack(side="left")

        self.display_count_var = tk.StringVar()
        ttk.Label(status_frame, textvariable=self.display_count_var).pack(side="right")

    # ── Canvas helpers ────────────────────────────────────────────────────────

    def draw_grid(self, event=None):
        self.canvas.delete("grid")
        w = self.canvas.winfo_width() or 800
        h = self.canvas.winfo_height() or 600
        for x in range(0, w, 50):
            self.canvas.create_line(x, 0, x, h, fill="#E8E8E8", tags="grid")
        for y in range(0, h, 50):
            self.canvas.create_line(0, y, w, y, fill="#E8E8E8", tags="grid")
        self.canvas.tag_raise("display")
        self.canvas.tag_raise("display_text")

    def _recenter(self):
        self._refit_view()
        self._redraw_all()
        self.draw_grid()

    def _on_canvas_configure(self, event=None):
        if self._any_drag_active():
            return                      # never yank items out from under a drag
        self._recenter()

    def _on_scale_change(self, value=None):
        if self.scale_label:
            self.scale_label.configure(text=f"{int(self.scale_var.get() * 100)}%")
        if self._any_drag_active():
            return
        self.scale = self.scale_var.get()
        self._recenter()

    # ── Display management ───────────────────────────────────────────────────

    def refresh_displays(self, confirm_discard: bool = True):
        if (confirm_discard and self._unsaved_changes
                and not messagebox.askyesno(
                    "Discard Changes?",
                    "You have unsaved arrangement changes.\nRefreshing will discard them. Continue?")):
            return
        self.status_var.set("Detecting displays…")
        self.root.update_idletasks()
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
            d = DraggableDisplay(self.canvas, display, view=self)
            d.add_callback('position_changed', self.on_display_position_changed)
            d.add_callback('drag_finished', self.on_display_drag_finished)
            self.draggable_displays[display_id] = d

        self._recenter()

    def on_display_config_change(self, display: Display, config: Dict):
        """Handle config panel changes — update model and redraw."""
        became_main = config['is_main'] and not display.is_main
        lost_main = display.is_main and not config['is_main']

        display.resolution = config['resolution']
        display.hz = config['hz']
        display.scaling = config['scaling']
        display.is_main = config['is_main']
        display.rotation = config['rotation']
        display.color_depth = config['color_depth']

        if became_main:
            # Exactly one main display: uncheck the others
            for other_id, other in self.draggable_displays.items():
                if other.display.id != display.id and other.display.is_main:
                    other.display.is_main = False
                    if other_id in self.config_panels:
                        self.config_panels[other_id].set_main_checkbox(False)
                    other.update_visual()
        elif lost_main:
            # macOS always has exactly one main display — to change it,
            # check "Set as Main" on another display instead.
            display.is_main = True
            if display.id in self.config_panels:
                self.config_panels[display.id].set_main_checkbox(True)
            self.status_var.set(
                "There must be one main display — set another display as main instead")

        if display.id in self.draggable_displays:
            self.draggable_displays[display.id].update_visual()
        self.draw_grid()

        self.status_var.set("Configuration updated — drag to position, then Save")
        self._mark_dirty()

    def on_display_position_changed(self, display: Display):
        """Live during drag: keep the sidebar position label in sync."""
        if display.id in self.config_panels:
            x, y = display.current_position
            self.config_panels[display.id].update_position_display(x, y)

    def on_display_drag_finished(self, display: Display, moved: bool):
        if not moved:
            return
        self._mark_dirty()
        rects = self._all_rects()
        if overlaps(rects):
            self.status_var.set(
                f"Moved {display.name} — ⚠ displays overlap; drag them apart before applying")
        elif not is_contiguous(rects):
            self.status_var.set(
                f"Moved {display.name} — ⚠ displays have a gap; macOS will close it on apply")
        else:
            self.status_var.set(f"Moved {display.name} to {display.current_position}")

    # ── Dirty / clean state ──────────────────────────────────────────────────

    def _mark_dirty(self):
        if not self._unsaved_changes:
            self._unsaved_changes = True
            self._unsaved_label.configure(text="(unsaved changes)")

    def _mark_clean(self):
        self._unsaved_changes = False
        self._unsaved_label.configure(text="")

    # ── Arrangement helpers ──────────────────────────────────────────────────

    def _sync_all_position_labels(self):
        for d in self.draggable_displays.values():
            if d.display.id in self.config_panels:
                x, y = d.display.current_position
                self.config_panels[d.display.id].update_position_display(x, y)

    def auto_arrange_displays(self):
        """Main display at (0,0), the rest in a row to its right, tops aligned."""
        displays = list(self.draggable_displays.values())
        if not displays:
            return
        main = next((d for d in displays if d.display.is_main), displays[0])
        others = [d for d in displays if d is not main]
        others.sort(key=lambda d: d.display.current_position[0])

        main.set_position(0, 0)
        x_offset = main.display.resolution[0]
        for d in others:
            d.set_position(x_offset, 0)
            x_offset += d.display.resolution[0]

        self._after_programmatic_arrange("Auto arranged")

    def align_horizontal(self):
        """One row, left-to-right in current order, tops aligned with the main."""
        if not self.draggable_displays:
            return
        ordered = sorted(self.draggable_displays.values(),
                         key=lambda d: d.display.current_position[0])
        ref_y = next(
            (d.display.current_position[1] for d in self.draggable_displays.values()
             if d.display.is_main), 0)
        x = min(d.display.current_position[0] for d in ordered)
        for d in ordered:
            d.set_position(x, ref_y)
            x += d.display.resolution[0]
        self._after_programmatic_arrange("Aligned in a row")

    def align_vertical(self):
        """One column, top-to-bottom in current order, lefts aligned with the main."""
        if not self.draggable_displays:
            return
        ordered = sorted(self.draggable_displays.values(),
                         key=lambda d: d.display.current_position[1])
        ref_x = next(
            (d.display.current_position[0] for d in self.draggable_displays.values()
             if d.display.is_main), 0)
        y = min(d.display.current_position[1] for d in ordered)
        for d in ordered:
            d.set_position(ref_x, y)
            y += d.display.resolution[1]
        self._after_programmatic_arrange("Stacked in a column")

    def _after_programmatic_arrange(self, status: str):
        self._sync_all_position_labels()
        self._recenter()
        self.status_var.set(status)
        self._mark_dirty()

    # ── Layout persistence ───────────────────────────────────────────────────

    def _collect_config(self) -> Dict[str, Dict]:
        """Current edited state: panel settings + canvas positions."""
        config: Dict[str, Dict] = {}
        for display_id, panel in self.config_panels.items():
            cfg = panel.get_config()
            if display_id in self.draggable_displays:
                cfg['position'] = self.draggable_displays[display_id].display.current_position
            config[display_id] = cfg
        return config

    def save_current_layout(self):
        pre = self.current_layout_name.get() or ""
        name = simpledialog.askstring("Save Layout", "Layout name:", initialvalue=pre)
        if not name:
            return
        description = simpledialog.askstring(
            "Save Layout", "Description (optional):", initialvalue="") or ""

        # Save what is on the canvas (the edited state), not the live OS state
        if self.display_manager.save_layout_from_config(name, description,
                                                        self._collect_config()):
            self.current_layout_name.set(name)
            self._mark_clean()
            self.status_var.set(f"Layout '{name}' saved")
        else:
            messagebox.showerror("Save Failed", "Could not save the layout.")

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
            draggable.display.resolution = tuple(config.get('resolution', draggable.display.resolution))
            draggable.display.scaling = config.get('scaling', draggable.display.scaling)
            draggable.display.is_main = config.get('is_main', draggable.display.is_main)
            draggable.display.hz = config.get('hz', draggable.display.hz)
            draggable.display.rotation = config.get('rotation', draggable.display.rotation)
            draggable.display.color_depth = config.get('color_depth', draggable.display.color_depth)
            draggable.display.current_position = (position[0], position[1])
            draggable.update_visual()

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

        self._recenter()
        self.current_layout_name.set(layout_name)
        self._mark_clean()
        self.status_var.set(f"Layout '{layout_name}' loaded — Apply to make it real")

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
        rects = self._all_rects()
        if overlaps(rects):
            messagebox.showerror("Displays Overlap",
                                 "Two or more displays overlap on the canvas.\n"
                                 "Drag them apart (edges snap together) before applying.")
            return
        warning = ""
        if not is_contiguous(rects):
            warning = "\n\nNote: there are gaps between displays — macOS will close them."
        if not messagebox.askyesno("Apply Arrangement",
                                   "Apply the current display arrangement now?\n"
                                   "Your monitors will rearrange." + warning):
            return

        success = self.display_manager.apply_display_config(self._collect_config())

        if success:
            self.status_var.set("Arrangement applied")
            # Re-detect so the canvas shows what macOS actually settled on
            self.refresh_displays(confirm_discard=False)
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
