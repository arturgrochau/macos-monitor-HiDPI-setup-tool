"""
Advanced Display Manager
Enhanced display management with dynamic detection and layout persistence.
"""

import subprocess
import json
import os
from typing import Dict, List, Optional, Tuple
import re
from dataclasses import dataclass, asdict

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
    
    DISPLAYPLACER = "/opt/homebrew/bin/displayplacer"
    LAYOUTS_FILE = os.path.expanduser("~/.monitor_layouts.json")
    
    def __init__(self):
        self.displays: Dict[str, Display] = {}
        self.layouts: Dict[str, LayoutProfile] = {}
        self.load_layouts()
    
    def detect_displays(self) -> Dict[str, Display]:
        """Detect all connected displays and their properties"""
        try:
            output = subprocess.check_output([self.DISPLAYPLACER, "list"], text=True)
            self.displays = self._parse_display_output(output)
            return self.displays
        except subprocess.CalledProcessError as e:
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
                
            display = self._parse_display_section(section)
            if display:
                displays[display.id] = display
        
        return displays
    
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
            
            if line.startswith("Persistent screen id:"):
                display_id = line.split(": ")[1]
            elif line.startswith("Type:"):
                if "MacBook" in line:
                    display_type = "macbook"
                    name = "MacBook Display"
                elif "inch external" in line:
                    name = f"External Display ({line.split()[1]} inch)"
                else:
                    name = "External Display"
            elif line.startswith("Resolution:"):
                res_str = line.split(": ")[1]
                w, h = res_str.split("x")
                resolution = (int(w), int(h))
            elif line.startswith("Origin:"):
                origin_str = line.split(": ")[1]
                # Parse (x,y) format, handle main display indicator
                origin_str = origin_str.split(" - ")[0]  # Remove main display indicator
                coords = origin_str.strip("()")
                x, y = coords.split(",")
                position = (int(x), int(y))
                is_main = "main display" in line
            elif line.startswith("Rotation:"):
                rotation = int(line.split(": ")[1].split()[0])
            elif line.startswith("Scaling:"):
                scaling = "on" in line.split(": ")[1]
            elif line.startswith("Hertz:"):
                hz_str = line.split(": ")[1]
                if hz_str != "N/A":
                    hz = int(hz_str)
            elif line.startswith("Color Depth:"):
                color_depth = int(line.split(": ")[1])
            elif line.startswith("Enabled:"):
                enabled = "true" in line.split(": ")[1]
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
    
    def apply_layout(self, layout_name: str) -> bool:
        """Apply a saved layout"""
        if layout_name not in self.layouts:
            print(f"Layout '{layout_name}' not found")
            return False
        
        layout = self.layouts[layout_name]
        commands = []
        
        for display_id, config in layout.displays.items():
            if display_id in self.displays and self.displays[display_id].enabled:
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
                    cmd_parts.append(f"origin:({x},{y})")
                
                if 'rotation' in config:
                    cmd_parts.append(f"degree:{config['rotation']}")
                
                commands.append(" ".join(cmd_parts))
        
        return self._execute_displayplacer_commands(commands)
    
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
        
        from datetime import datetime
        layout = LayoutProfile(
            name=name,
            description=description,
            displays=layout_config,
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
        if os.path.exists(self.LAYOUTS_FILE):
            try:
                with open(self.LAYOUTS_FILE, 'r') as f:
                    data = json.load(f)
                    for name, layout_data in data.items():
                        self.layouts[name] = LayoutProfile(**layout_data)
            except Exception as e:
                print(f"Error loading layouts: {e}")
    
    def save_layouts(self):
        """Save layouts to disk"""
        try:
            data = {}
            for name, layout in self.layouts.items():
                data[name] = asdict(layout)
            
            with open(self.LAYOUTS_FILE, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving layouts: {e}")
    
    def _execute_displayplacer_commands(self, commands: List[str]) -> bool:
        """Execute displayplacer commands"""
        try:
            for cmd in commands:
                full_cmd = f'{self.DISPLAYPLACER} "{cmd}"'
                print(f"Executing: {full_cmd}")
                result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True)
                if result.returncode != 0:
                    print(f"Command failed: {result.stderr}")
                    return False
            return True
        except Exception as e:
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
