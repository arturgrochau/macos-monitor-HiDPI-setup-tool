"""
Advanced Display Manager
Enhanced display management with dynamic detection and layout persistence.
"""

import subprocess
import json
import os
import sys
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import re
from dataclasses import dataclass, asdict

from utils.displayplacer import find_displayplacer

@dataclass
class Display:
    """Represents a display with all its properties"""
    id: str
    name: str
    type: str  # "macbook", "external"
    resolution: Tuple[int, int]
    available_resolutions: List[Tuple[int, int]]
    current_position: Tuple[int, int]
    rotation: int
    scaling: bool
    hz: int
    color_depth: int
    enabled: bool
    is_main: bool

@dataclass
class LayoutProfile:
    """Represents a saved layout configuration"""
    name: str
    description: str
    displays: Dict[str, Dict]  # Display ID -> configuration
    created_at: str
    last_used: str = ""

class AdvancedDisplayManager:
    """Advanced display manager with dynamic detection and layout persistence"""

    LAYOUTS_FILE = os.path.expanduser("~/.monitor_layouts.json")

    def __init__(self, layouts_file: str | None = None):
        self.DISPLAYPLACER = find_displayplacer()
        self.layouts_file = layouts_file if layouts_file is not None else self.LAYOUTS_FILE
        self.displays: Dict[str, Display] = {}
        self.layouts: Dict[str, LayoutProfile] = {}
        self.load_layouts()

    def detect_displays(self) -> Dict[str, Display]:
        """Detect all connected displays and their properties"""
        if not self.DISPLAYPLACER:
            print("Error: displayplacer not found. Install with: brew install jakehilborn/jakehilborn/displayplacer")
            return {}
        try:
            output = subprocess.check_output([self.DISPLAYPLACER, "list"], text=True, timeout=15)
            self.displays = self._parse_display_output(output)
            return self.displays
        except subprocess.CalledProcessError as e:
            print(f"Error detecting displays: {e}")
            return {}
        except subprocess.TimeoutExpired:
            print("Error detecting displays: displayplacer timed out")
            return {}
        except (FileNotFoundError, OSError) as e:
            # The cached displayplacer path can vanish between discovery and use
            print(f"Error detecting displays: {e}")
            return {}
    
    def _parse_display_output(self, output: str) -> Dict[str, Display]:
        """Parse displayplacer list output into Display objects"""
        displays = {}
        
        # Split output into sections for each display
        sections = re.split(r'\n(?=Persistent screen id:)', output.strip())
        
        for section in sections:
            if not section.strip():
                continue

            try:
                display = self._parse_display_section(section)
            except Exception as e:
                first_line = section.strip().splitlines()[0] if section.strip() else ""
                print(
                    f"Warning: skipping unparseable display section ({e}): {first_line}",
                    file=sys.stderr,
                )
                continue
            if display:
                displays[display.id] = display

        return displays

    @staticmethod
    def _value_after_colon(line: str) -> Optional[str]:
        """Return the value after 'Key: ' in a displayplacer line, or None.

        Defensive against format drift — never raises IndexError.
        """
        parts = line.split(": ", 1)
        if len(parts) != 2:
            return None
        return parts[1].strip()

    def _parse_display_section(self, section: str) -> Optional[Display]:
        """Parse a single display section"""
        lines = section.strip().split('\n')
        
        display_id = ""
        name = ""
        display_type = "external"
        resolution = (1920, 1080)
        position = (0, 0)
        rotation = 0
        scaling = False
        hz = 60
        color_depth = 8
        enabled = True
        is_main = False
        available_resolutions = []
        
        for line in lines:
            line = line.strip()
            
            value = self._value_after_colon(line)

            if line.startswith("Persistent screen id:"):
                if value:
                    display_id = value
            elif line.startswith("Type:"):
                if "MacBook" in line:
                    display_type = "macbook"
                    name = "MacBook Display"
                elif "inch external" in line:
                    name = f"External Display ({line.split()[1]} inch)"
                else:
                    name = "External Display"
            elif line.startswith("Resolution:"):
                if value and "x" in value:
                    w, h = value.split("x")
                    resolution = (int(w), int(h))
            elif line.startswith("Origin:"):
                if value:
                    # Parse (x,y) format, handle main display indicator
                    origin_str = value.split(" - ")[0]  # Remove main display indicator
                    coords = origin_str.strip("()")
                    x, y = coords.split(",")
                    position = (int(x), int(y))
                    is_main = "main display" in line
            elif line.startswith("Rotation:"):
                if value:
                    rotation = int(value.split()[0])
            elif line.startswith("Scaling:"):
                if value:
                    scaling = "on" in value
            elif line.startswith("Hertz:"):
                if value and value != "N/A":
                    hz = int(value)
            elif line.startswith("Color Depth:"):
                if value:
                    color_depth = int(value)
            elif line.startswith("Enabled:"):
                if value:
                    enabled = "true" in value
            elif "mode" in line and "res:" in line:
                # Parse available resolutions
                match = re.search(r'res:(\d+)x(\d+)', line)
                if match:
                    w, h = int(match.group(1)), int(match.group(2))
                    if (w, h) not in available_resolutions:
                        available_resolutions.append((w, h))
        
        if not display_id:
            return None
            
        return Display(
            id=display_id,
            name=name,
            type=display_type,
            resolution=resolution,
            available_resolutions=available_resolutions or [resolution],
            current_position=position,
            rotation=rotation,
            scaling=scaling,
            hz=hz,
            color_depth=color_depth,
            enabled=enabled,
            is_main=is_main
        )
    
    def apply_display_config(self, displays_config: Dict[str, Dict]) -> bool:
        """Apply a display configuration dict immediately.

        Never touches self.layouts or the layouts file — callers that want
        persistence (apply_layout) handle that themselves.
        """
        def connected(display_id: str) -> bool:
            return display_id in self.displays and self.displays[display_id].enabled

        # displayplacer origins are relative to the main display's top-left
        # (0,0). If the config marks a connected display as main, re-normalize
        # every origin so it lands exactly at (0,0) with relative offsets
        # preserved. If the marked main is not connected, anchor to the first
        # connected display instead so the applied arrangement still has a
        # display at (0,0). If no display claims main, keep origins as-is.
        offset_x, offset_y = 0, 0
        main_ids = [did for did, c in displays_config.items()
                    if c.get('is_main') and 'position' in c]
        if main_ids:
            anchor = next((did for did in main_ids if connected(did)), None)
            if anchor is None:
                anchor = next((did for did, c in displays_config.items()
                               if connected(did) and 'position' in c), None)
            if anchor is not None:
                offset_x, offset_y = displays_config[anchor]['position']

        commands = []

        for display_id, config in displays_config.items():
            if connected(display_id):
                cmd_parts = [f"id:{display_id}"]

                if 'resolution' in config:
                    w, h = config['resolution']
                    cmd_parts.append(f"res:{w}x{h}")

                if 'hz' in config:
                    cmd_parts.append(f"hz:{config['hz']}")

                if 'color_depth' in config:
                    cmd_parts.append(f"color_depth:{config['color_depth']}")

                if 'scaling' in config:
                    cmd_parts.append(f"scaling:{'on' if config['scaling'] else 'off'}")

                if 'position' in config:
                    x, y = config['position']
                    cmd_parts.append(f"origin:({x - offset_x},{y - offset_y})")

                if 'rotation' in config:
                    cmd_parts.append(f"degree:{config['rotation']}")

                commands.append(" ".join(cmd_parts))

        if not commands:
            print("No displays from this configuration are currently connected — nothing to apply")
            return False

        return self._execute_displayplacer_commands(commands)

    def apply_layout(self, layout_name: str) -> bool:
        """Apply a saved layout"""
        if layout_name not in self.layouts:
            print(f"Layout '{layout_name}' not found")
            return False

        layout = self.layouts[layout_name]
        success = self.apply_display_config(layout.displays)
        if success:
            layout.last_used = datetime.now().isoformat()
            self.save_layouts()
        return success
    
    def save_layout(self, name: str, description: str = "") -> bool:
        """Save current display configuration as a layout"""
        current_displays = self.detect_displays()
        
        if not current_displays:
            print("No displays detected to save")
            return False
        
        layout_config = {}
        for display_id, display in current_displays.items():
            if display.enabled:
                layout_config[display_id] = {
                    'resolution': display.resolution,
                    'position': display.current_position,
                    'rotation': display.rotation,
                    'scaling': display.scaling,
                    'hz': display.hz,
                    'color_depth': display.color_depth,
                    'is_main': display.is_main
                }
        
        layout = LayoutProfile(
            name=name,
            description=description,
            displays=layout_config,
            created_at=datetime.now().isoformat()
        )

        self.layouts[name] = layout
        self.save_layouts()
        return True

    def save_layout_from_config(self, name: str, description: str,
                                displays_config: Dict[str, Dict]) -> bool:
        """Save a layout from a provided configuration dict (no re-detection).

        displays_config maps display id -> dict with keys such as
        resolution, position, hz, scaling, is_main, rotation, color_depth.
        Used by the GUI so user edits are persisted exactly as arranged.
        """
        if not displays_config:
            print("No display configuration provided to save")
            return False

        layout = LayoutProfile(
            name=name,
            description=description,
            displays=displays_config,
            created_at=datetime.now().isoformat()
        )

        self.layouts[name] = layout
        self.save_layouts()
        return True


    def delete_layout(self, name: str) -> bool:
        """Delete a saved layout"""
        if name in self.layouts:
            del self.layouts[name]
            self.save_layouts()
            return True
        return False
    
    def get_layout_names(self) -> List[str]:
        """Get list of saved layout names"""
        return list(self.layouts.keys())
    
    def get_layout(self, name: str) -> Optional[LayoutProfile]:
        """Get a specific layout"""
        return self.layouts.get(name)
    
    def load_layouts(self):
        """Load saved layouts from disk"""
        if os.path.exists(self.layouts_file):
            try:
                with open(self.layouts_file, 'r') as f:
                    data = json.load(f)
                    for name, layout_data in data.items():
                        self.layouts[name] = LayoutProfile(**layout_data)
            except (OSError, json.JSONDecodeError, TypeError) as e:
                print(f"Error loading layouts: {e}")
    
    def save_layouts(self):
        """Save layouts to disk"""
        try:
            data = {}
            for name, layout in self.layouts.items():
                data[name] = asdict(layout)
            
            with open(self.layouts_file, 'w') as f:
                json.dump(data, f, indent=2)
        except (OSError, TypeError) as e:
            print(f"Error saving layouts: {e}")
    
    def _execute_displayplacer_commands(self, commands: List[str]) -> bool:
        """Execute displayplacer commands.

        displayplacer takes each display config as a separate quoted argument:
          displayplacer "id:A res:..." "id:B res:..."
        We pass all configs in one call so it sets all displays atomically.
        """
        if not self.DISPLAYPLACER:
            print("Error: displayplacer not found")
            return False
        if not commands:
            return True
        try:
            result = subprocess.run(
                [self.DISPLAYPLACER] + commands,
                capture_output=True, text=True, timeout=30, check=False
            )
            if result.returncode != 0:
                print(f"displayplacer failed: {result.stderr.strip()}")
                return False
            return True
        except subprocess.TimeoutExpired:
            print("Error executing commands: displayplacer timed out after 30s")
            return False
        except (FileNotFoundError, OSError) as e:
            print(f"Error executing commands: {e}")
            return False
    
    def create_preview_layout(self, display_configs: Dict[str, Dict]) -> Dict[str, Dict]:
        """Create a preview of how displays would be arranged"""
        preview = {}
        
        for display_id, config in display_configs.items():
            if display_id in self.displays:
                display = self.displays[display_id]
                preview[display_id] = {
                    'name': display.name,
                    'type': display.type,
                    'resolution': config.get('resolution', display.resolution),
                    'position': config.get('position', display.current_position),
                    'scaling': config.get('scaling', display.scaling),
                    'rotation': config.get('rotation', display.rotation),
                    'is_main': config.get('is_main', display.is_main),
                    'enabled': True
                }
        
        return preview
