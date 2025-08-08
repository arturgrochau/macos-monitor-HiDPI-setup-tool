# MIT License
# Copyright (c) 2025 Artur Grochau
# 
# This file is part of Monitor Layout Manager.
# See the LICENSE file in the root directory for full license text.

"""
Helper Utilities Module - Common utility functions
Shared functionality across the Monitor Layout Manager application
"""

import subprocess
import re
import json
import os
from typing import Dict, List, Tuple, Optional
from datetime import datetime

def validate_displayplacer_installation(path: str = "/opt/homebrew/bin/displayplacer") -> bool:
    """Validate that displayplacer is properly installed"""
    try:
        result = subprocess.run([path, "--version"], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False

def get_displayplacer_help(path: str = "/opt/homebrew/bin/displayplacer") -> str:
    """Get displayplacer help information"""
    try:
        result = subprocess.run([path, "--help"], capture_output=True, text=True)
        return result.stdout if result.returncode == 0 else "Help not available"
    except FileNotFoundError:
        return "DisplayPlacer not found"

def parse_resolution_string(res_string: str) -> Tuple[int, int]:
    """Parse resolution string like '1920x1080' into tuple"""
    try:
        parts = res_string.lower().split('x')
        if len(parts) == 2:
            return int(parts[0]), int(parts[1])
    except (ValueError, IndexError):
        pass
    return 1920, 1080  # Default fallback

def format_resolution(resolution: Tuple[int, int]) -> str:
    """Format resolution tuple as string"""
    return f"{resolution[0]}×{resolution[1]}"

def calculate_display_bounds(displays: Dict[str, Dict]) -> Dict[str, int]:
    """Calculate the overall bounds of all displays"""
    if not displays:
        return {"min_x": 0, "max_x": 0, "min_y": 0, "max_y": 0, "width": 0, "height": 0}
    
    min_x = min(display["position"][0] for display in displays.values())
    max_x = max(display["position"][0] + display["resolution"][0] for display in displays.values())
    min_y = min(display["position"][1] for display in displays.values())
    max_y = max(display["position"][1] + display["resolution"][1] for display in displays.values())
    
    return {
        "min_x": min_x,
        "max_x": max_x,
        "min_y": min_y,
        "max_y": max_y,
        "width": max_x - min_x,
        "height": max_y - min_y
    }

def detect_display_arrangement_type(displays: Dict[str, Dict]) -> str:
    """Detect the arrangement type of displays"""
    if len(displays) <= 1:
        return "single"
    
    positions = [display["position"] for display in displays.values()]
    
    # Check if all displays are horizontally aligned (same Y coordinate)
    y_coords = [pos[1] for pos in positions]
    if len(set(y_coords)) == 1:
        return "horizontal"
    
    # Check if all displays are vertically aligned (same X coordinate)
    x_coords = [pos[0] for pos in positions]
    if len(set(x_coords)) == 1:
        return "vertical"
    
    # Check for L-shape or complex arrangements
    return "complex"

def suggest_optimal_arrangement(displays: List[Dict]) -> List[Dict]:
    """Suggest an optimal arrangement for displays"""
    if len(displays) <= 1:
        return displays
    
    # Sort by resolution (largest first) and type (external first)
    sorted_displays = sorted(displays, key=lambda d: (
        d.get("type") != "external",  # External displays first
        -d["resolution"][0] * d["resolution"][1]  # Larger resolution first
    ))
    
    # Position displays horizontally from left to right
    current_x = 0
    arranged_displays = []
    
    for display in sorted_displays:
        arranged_display = display.copy()
        arranged_display["position"] = (current_x, 0)
        arranged_displays.append(arranged_display)
        current_x += display["resolution"][0]
    
    return arranged_displays

def generate_displayplacer_command(display_config: Dict) -> str:
    """Generate displayplacer command for a display configuration"""
    parts = [f"id:{display_config['id']}"]
    
    if 'resolution' in display_config:
        w, h = display_config['resolution']
        parts.append(f"res:{w}x{h}")
    
    if 'hz' in display_config and display_config['hz']:
        parts.append(f"hz:{display_config['hz']}")
    
    if 'color_depth' in display_config:
        parts.append(f"color_depth:{display_config['color_depth']}")
    
    if 'scaling' in display_config:
        scaling = "on" if display_config['scaling'] else "off"
        parts.append(f"scaling:{scaling}")
    
    if 'position' in display_config:
        x, y = display_config['position']
        parts.append(f"origin:({x},{y})")
    
    if 'rotation' in display_config and display_config['rotation']:
        parts.append(f"degree:{display_config['rotation']}")
    
    if display_config.get('enabled', True):
        parts.append("enabled:true")
    else:
        parts.append("enabled:false")
    
    return " ".join(parts)

def backup_current_layout(backup_dir: str = None) -> str:
    """Backup current display layout"""
    if backup_dir is None:
        backup_dir = os.path.expanduser("~/.monitor_layout_backups")
    
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(backup_dir, f"layout_backup_{timestamp}.json")
    
    try:
        # Get current layout using displayplacer
        result = subprocess.run(["/opt/homebrew/bin/displayplacer", "list"], 
                               capture_output=True, text=True)
        
        if result.returncode == 0:
            backup_data = {
                "timestamp": datetime.now().isoformat(),
                "displayplacer_output": result.stdout,
                "backup_type": "automatic"
            }
            
            with open(backup_file, 'w') as f:
                json.dump(backup_data, f, indent=2)
            
            return backup_file
    except Exception as e:
        print(f"Error creating backup: {e}")
    
    return ""

def restore_layout_from_backup(backup_file: str) -> bool:
    """Restore layout from backup file"""
    try:
        with open(backup_file, 'r') as f:
            backup_data = json.load(f)
        
        # This would need more sophisticated parsing to extract the actual commands
        # For now, just return True to indicate the file was read successfully
        print(f"Backup from {backup_data.get('timestamp')} loaded")
        return True
    except Exception as e:
        print(f"Error restoring backup: {e}")
        return False

def get_display_vendor_info(display_output: str) -> Dict[str, str]:
    """Extract vendor information from display output"""
    vendor_info = {}
    
    # Look for vendor/model information in the display output
    for line in display_output.split('\n'):
        if 'Type:' in line and 'inch external' in line:
            # Try to extract size information
            size_match = re.search(r'(\d+) inch', line)
            if size_match:
                vendor_info['size'] = f"{size_match.group(1)} inch"
        elif 'DisplayVendorID' in line:
            vendor_match = re.search(r'DisplayVendorID-(\w+)', line)
            if vendor_match:
                vendor_info['vendor_id'] = vendor_match.group(1)
        elif 'DisplayProductID' in line:
            product_match = re.search(r'DisplayProductID-(\w+)', line)
            if product_match:
                vendor_info['product_id'] = product_match.group(1)
    
    return vendor_info

def calculate_ppi(resolution: Tuple[int, int], diagonal_inches: float) -> float:
    """Calculate pixels per inch for a display"""
    if diagonal_inches <= 0:
        return 0.0
    
    width, height = resolution
    diagonal_pixels = (width ** 2 + height ** 2) ** 0.5
    return diagonal_pixels / diagonal_inches

def is_hidpi_recommended(resolution: Tuple[int, int], size_inches: float = None) -> bool:
    """Determine if HiDPI scaling is recommended for a display"""
    if size_inches:
        ppi = calculate_ppi(resolution, size_inches)
        return ppi > 200  # Generally HiDPI is beneficial above 200 PPI
    
    # Fallback based on resolution
    width, height = resolution
    return width >= 2560 or height >= 1440

def find_common_resolutions() -> List[Tuple[int, int]]:
    """Return list of common display resolutions"""
    return [
        (1280, 720),    # HD
        (1366, 768),    # WXGA
        (1440, 900),    # WXGA+
        (1680, 1050),   # WSXGA+
        (1920, 1080),   # Full HD
        (1920, 1200),   # WUXGA
        (2560, 1440),   # QHD
        (2560, 1600),   # WQXGA
        (3440, 1440),   # UWQHD
        (3840, 2160),   # 4K UHD
        (5120, 2880),   # 5K
    ]

def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024**2:
        return f"{size_bytes/1024:.1f} KB"
    elif size_bytes < 1024**3:
        return f"{size_bytes/1024**2:.1f} MB"
    else:
        return f"{size_bytes/1024**3:.1f} GB"

def validate_layout_file(file_path: str) -> bool:
    """Validate that a layout file is properly formatted"""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Check for required fields
        if not isinstance(data, dict):
            return False
        
        # Check if it's a layout backup or settings file
        if 'timestamp' in data or 'displayplacer_output' in data:
            return True  # Backup file
        
        # Check if it's a layout collection
        for key, value in data.items():
            if isinstance(value, dict):
                required_fields = ['name', 'displays', 'created_at']
                if all(field in value for field in required_fields):
                    return True
        
        return False
    except Exception:
        return False

def get_system_theme() -> str:
    """Detect system theme (light/dark) on macOS"""
    try:
        result = subprocess.run([
            'defaults', 'read', '-g', 'AppleInterfaceStyle'
        ], capture_output=True, text=True)
        
        if result.returncode == 0 and 'Dark' in result.stdout:
            return 'dark'
        else:
            return 'light'
    except Exception:
        return 'light'  # Default fallback

def center_window(window, width: int = None, height: int = None):
    """Center a Tkinter window on screen"""
    window.update_idletasks()
    
    if width is None:
        width = window.winfo_width()
    if height is None:
        height = window.winfo_height()
    
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    
    window.geometry(f"{width}x{height}+{x}+{y}")

def create_desktop_shortcut(app_path: str, shortcut_name: str = "Monitor Layout Manager"):
    """Create a desktop shortcut (macOS specific)"""
    try:
        desktop_path = os.path.expanduser("~/Desktop")
        shortcut_path = os.path.join(desktop_path, f"{shortcut_name}.command")
        
        shortcut_content = f"""#!/bin/bash
cd "{os.path.dirname(app_path)}"
python3 "{app_path}"
"""
        
        with open(shortcut_path, 'w') as f:
            f.write(shortcut_content)
        
        # Make executable
        os.chmod(shortcut_path, 0o755)
        return shortcut_path
    except Exception as e:
        print(f"Error creating desktop shortcut: {e}")
        return None
