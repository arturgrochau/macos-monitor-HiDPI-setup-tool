"""
Utility functions for the Monitor Layout Manager
"""

import subprocess
import json
import os
from typing import Dict, Tuple
from datetime import datetime

from utils.displayplacer import find_displayplacer


def validate_displayplacer_installation(path: str | None = None) -> bool:
    """Validate that displayplacer is installed and runnable."""
    if path is None:
        path = find_displayplacer()
    if path is None:
        return False
    try:
        result = subprocess.run([path, "--version"], capture_output=True, text=True,
                                timeout=5, check=False)
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return False


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


def backup_current_layout(backup_dir: str | None = None) -> str:
    """Backup current display layout"""
    if backup_dir is None:
        backup_dir = os.path.expanduser("~/.monitor_layout_backups")

    os.makedirs(backup_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(backup_dir, f"layout_backup_{timestamp}.json")

    dp_path = find_displayplacer()
    try:
        if dp_path is None:
            return ""
        result = subprocess.run([dp_path, "list"],
                                capture_output=True, text=True,
                                timeout=10, check=False)

        if result.returncode == 0:
            backup_data = {
                "timestamp": datetime.now().isoformat(),
                "displayplacer_output": result.stdout,
                "backup_type": "automatic"
            }

            with open(backup_file, 'w') as f:
                json.dump(backup_data, f, indent=2)

            return backup_file
    except (subprocess.TimeoutExpired, OSError) as e:
        print(f"Error creating backup: {e}")

    return ""


def calculate_ppi(resolution: Tuple[int, int], diagonal_inches: float) -> float:
    """Calculate pixels per inch for a display"""
    if diagonal_inches <= 0:
        return 0.0

    width, height = resolution
    diagonal_pixels = (width ** 2 + height ** 2) ** 0.5
    return diagonal_pixels / diagonal_inches


def is_hidpi_recommended(resolution: Tuple[int, int], size_inches: float | None = None) -> bool:
    """Determine if HiDPI scaling is recommended for a display"""
    if size_inches:
        ppi = calculate_ppi(resolution, size_inches)
        return ppi > 200  # Generally HiDPI is beneficial above 200 PPI

    # Fallback based on resolution
    width, height = resolution
    return width >= 2560 or height >= 1440
