"""
Advanced CLI Interface for Monitor Layout Manager
"""

try:
    import click
except ImportError:
    print("❌ Missing dependency: click")
    print("💡 Run: ./install.sh or activate virtualenv + pip install -r requirements.txt")
    exit(1)

import json
import os
import sys
from typing import List, Dict
from datetime import datetime

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from core.advanced_display_manager import AdvancedDisplayManager
from utils.helpers import (
    validate_displayplacer_installation, 
    format_resolution, 
    backup_current_layout
)

def print_banner():
    """Print application banner"""
    banner = """
╭─────────────────────────────────────────────╮
│        Advanced Monitor Layout Manager      │
│              by GitHub Copilot               │
╰─────────────────────────────────────────────╯
    """
    click.echo(click.style(banner, fg='blue', bold=True))

@click.group()
@click.version_option(version='2.0.0')
@click.option("--debug", is_flag=True, help="Enable debug mode.")
@click.pass_context
def cli(ctx, debug):
    """Advanced Monitor Layout Manager - Command Line Interface"""
    ctx.ensure_object(dict)
    ctx.obj['debug'] = debug
    if debug:
        click.echo(click.style("🐛 Debug mode enabled", fg='yellow'))

@cli.command()
@click.option('--detailed', '-d', is_flag=True, help='Show detailed display information')
@click.option('--json-output', '-j', is_flag=True, help='Output in JSON format')
def detect(detailed, json_output):
    """Detect and display information about connected monitors"""
    if not validate_displayplacer_installation():
        click.echo(click.style("Error: displayplacer not found. Please install it first.", fg='red'))
        return
    
    manager = AdvancedDisplayManager()
    displays = manager.detect_displays()
    
    if not displays:
        click.echo(click.style("No displays detected.", fg='yellow'))
        return
    
    if json_output:
        display_data = {}
        for display_id, display in displays.items():
            display_data[display_id] = {
                'name': display.name,
                'type': display.type,
                'resolution': display.resolution,
                'position': display.current_position,
                'scaling': display.scaling,
                'is_main': display.is_main,
                'enabled': display.enabled
            }
        click.echo(json.dumps(display_data, indent=2))
        return
    
    click.echo(click.style(f"Found {len(displays)} display(s):", fg='green', bold=True))
    click.echo()
    
    for i, (display_id, display) in enumerate(displays.items(), 1):
        click.echo(f"{i}. {click.style(display.name, fg='cyan', bold=True)}")
        click.echo(f"   ID: {display_id[:8]}...")
        click.echo(f"   Type: {display.type.title()}")
        click.echo(f"   Resolution: {format_resolution(display.resolution)}")
        click.echo(f"   Position: ({display.current_position[0]}, {display.current_position[1]})")
        click.echo(f"   Refresh Rate: {display.hz}Hz")
        click.echo(f"   Scaling: {'On' if display.scaling else 'Off'}")
        click.echo(f"   Main Display: {'Yes' if display.is_main else 'No'}")
        click.echo(f"   Enabled: {'Yes' if display.enabled else 'No'}")
        
        if detailed:
            click.echo(f"   Available Resolutions: {len(display.available_resolutions)} modes")
            for res in display.available_resolutions[:5]:  # Show first 5
                click.echo(f"     - {format_resolution(res)}")
            if len(display.available_resolutions) > 5:
                click.echo(f"     ... and {len(display.available_resolutions) - 5} more")
        
        if i < len(displays):
            click.echo()

@cli.command()
@click.option('--name', '-n', required=True, help='Name for the new layout')
@click.option('--description', '-d', help='Description for the layout')
def save(name, description):
    """Save current display configuration as a layout"""
    manager = AdvancedDisplayManager()
    
    if manager.save_layout(name, description or ""):
        click.echo(click.style(f"✓ Layout '{name}' saved successfully!", fg='green'))
    else:
        click.echo(click.style(f"✗ Failed to save layout '{name}'", fg='red'))

@cli.command()
@click.argument('layout_name', required=False)
@click.option('--interactive', '-i', is_flag=True, help='Interactive layout selection')
def load(layout_name, interactive):
    """Load and apply a saved layout"""
    manager = AdvancedDisplayManager()
    layouts = manager.get_layout_names()
    
    if not layouts:
        click.echo(click.style("No saved layouts found.", fg='yellow'))
        return
    
    if interactive or not layout_name:
        click.echo("Available layouts:")
        for i, name in enumerate(layouts, 1):
            layout = manager.get_layout(name)
            click.echo(f"{i}. {click.style(name, fg='cyan')} - {layout.description}")
        
        if not layout_name:
            try:
                choice = click.prompt("Select layout number", type=int)
                if 1 <= choice <= len(layouts):
                    layout_name = layouts[choice - 1]
                else:
                    click.echo(click.style("Invalid selection.", fg='red'))
                    return
            except (ValueError, EOFError):
                click.echo(click.style("Cancelled.", fg='yellow'))
                return
    
    if layout_name not in layouts:
        click.echo(click.style(f"Layout '{layout_name}' not found.", fg='red'))
        similar = [name for name in layouts if layout_name.lower() in name.lower()]
        if similar:
            click.echo(f"Did you mean: {', '.join(similar)}")
        return
    
    click.echo(f"Applying layout '{layout_name}'...")
    
    if manager.apply_layout(layout_name):
        click.echo(click.style(f"✓ Layout '{layout_name}' applied successfully!", fg='green'))
    else:
        click.echo(click.style(f"✗ Failed to apply layout '{layout_name}'", fg='red'))

@cli.command()
def list_layouts():
    """List all saved layouts"""
    manager = AdvancedDisplayManager()
    layouts = manager.get_layout_names()
    
    if not layouts:
        click.echo(click.style("No saved layouts found.", fg='yellow'))
        return
    
    click.echo(click.style(f"Saved layouts ({len(layouts)}):", fg='blue', bold=True))
    click.echo()
    
    for name in layouts:
        layout = manager.get_layout(name)
        displays_count = len(layout.displays)
        created_date = datetime.fromisoformat(layout.created_at).strftime("%Y-%m-%d %H:%M")
        
        click.echo(f"• {click.style(name, fg='cyan', bold=True)}")
        click.echo(f"  Description: {layout.description or 'No description'}")
        click.echo(f"  Displays: {displays_count}")
        click.echo(f"  Created: {created_date}")
        if layout.last_used:
            last_used = datetime.fromisoformat(layout.last_used).strftime("%Y-%m-%d %H:%M")
            click.echo(f"  Last used: {last_used}")
        click.echo()

@cli.command()
@click.argument('layout_name')
@click.confirmation_option(prompt='Are you sure you want to delete this layout?')
def delete(layout_name):
    """Delete a saved layout"""
    manager = AdvancedDisplayManager()
    
    if manager.delete_layout(layout_name):
        click.echo(click.style(f"✓ Layout '{layout_name}' deleted.", fg='green'))
    else:
        click.echo(click.style(f"✗ Layout '{layout_name}' not found.", fg='red'))

@cli.command()
@click.option('--output', '-o', help='Output file path')
def export(output):
    """Export all layouts to a file"""
    manager = AdvancedDisplayManager()
    layouts = manager.get_layout_names()
    
    if not layouts:
        click.echo(click.style("No layouts to export.", fg='yellow'))
        return
    
    if not output:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = f"monitor_layouts_export_{timestamp}.json"
    
    try:
        from dataclasses import asdict
        
        export_data = {}
        for name in layouts:
            layout = manager.get_layout(name)
            export_data[name] = asdict(layout)
        
        with open(output, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        click.echo(click.style(f"✓ {len(layouts)} layout(s) exported to {output}", fg='green'))
    except Exception as e:
        click.echo(click.style(f"✗ Export failed: {e}", fg='red'))

@cli.command()
@click.argument('input_file')
@click.option('--merge', '-m', is_flag=True, help='Merge with existing layouts instead of replacing')
def import_layouts(input_file, merge):
    """Import layouts from a file"""
    if not os.path.exists(input_file):
        click.echo(click.style(f"File not found: {input_file}", fg='red'))
        return
    
    try:
        with open(input_file, 'r') as f:
            import_data = json.load(f)
        
        manager = AdvancedDisplayManager()
        
        if not merge:
            # Backup existing layouts first
            backup_file = backup_current_layout()
            if backup_file:
                click.echo(f"Existing layouts backed up to: {backup_file}")
        
        imported_count = 0
        for name, layout_data in import_data.items():
            if merge and name in manager.layouts:
                if not click.confirm(f"Layout '{name}' already exists. Overwrite?"):
                    continue
            
            layout = manager.LayoutProfile(**layout_data)
            manager.layouts[name] = layout
            imported_count += 1
        
        manager.save_layouts()
        click.echo(click.style(f"✓ {imported_count} layout(s) imported from {input_file}", fg='green'))
        
    except Exception as e:
        click.echo(click.style(f"✗ Import failed: {e}", fg='red'))

@cli.command()
def backup():
    """Create a backup of current display configuration"""
    backup_file = backup_current_layout()
    
    if backup_file:
        click.echo(click.style(f"✓ Backup created: {backup_file}", fg='green'))
    else:
        click.echo(click.style("✗ Failed to create backup", fg='red'))

@cli.command()
def gui():
    """Launch the graphical user interface"""
    try:
        from gui.advanced_layout_manager import AdvancedMonitorLayoutManager
        
        print_banner()
        click.echo("Launching GUI...")
        
        app = AdvancedMonitorLayoutManager()
        app.run()
        
    except ImportError:
        click.echo(click.style("GUI components not available. Install tkinter.", fg='red'))
    except Exception as e:
        click.echo(click.style(f"Error launching GUI: {e}", fg='red'))

@cli.command()
def doctor():
    """Diagnose potential issues with the setup"""
    click.echo(click.style("Running diagnostics...", fg='blue', bold=True))
    click.echo()
    
    issues_found = 0
    
    # Check displayplacer installation
    click.echo("1. Checking displayplacer installation...")
    if validate_displayplacer_installation():
        click.echo(click.style("   ✓ displayplacer found and working", fg='green'))
    else:
        click.echo(click.style("   ✗ displayplacer not found or not working", fg='red'))
        click.echo("     Install with: brew install jakehilborn/jakehilborn/displayplacer")
        issues_found += 1
    
    # Check permissions
    click.echo("2. Checking file permissions...")
    layouts_file = os.path.expanduser("~/.monitor_layouts.json")
    if os.path.exists(layouts_file):
        if os.access(layouts_file, os.R_OK | os.W_OK):
            click.echo(click.style("   ✓ Layouts file accessible", fg='green'))
        else:
            click.echo(click.style("   ✗ Layouts file permission issues", fg='red'))
            issues_found += 1
    else:
        click.echo(click.style("   ℹ No layouts file found (will be created)", fg='yellow'))
    
    # Check display detection
    click.echo("3. Testing display detection...")
    try:
        manager = AdvancedDisplayManager()
        displays = manager.detect_displays()
        if displays:
            click.echo(click.style(f"   ✓ {len(displays)} display(s) detected", fg='green'))
        else:
            click.echo(click.style("   ⚠ No displays detected", fg='yellow'))
    except Exception as e:
        click.echo(click.style(f"   ✗ Display detection failed: {e}", fg='red'))
        issues_found += 1
    
    # Check Python tkinter (for GUI)
    click.echo("4. Checking GUI dependencies...")
    try:
        import tkinter
        click.echo(click.style("   ✓ tkinter available for GUI", fg='green'))
    except ImportError:
        click.echo(click.style("   ✗ tkinter not available (GUI won't work)", fg='red'))
        issues_found += 1
    
    click.echo()
    if issues_found == 0:
        click.echo(click.style("All checks passed! Your setup looks good.", fg='green', bold=True))
    else:
        click.echo(click.style(f"Found {issues_found} issue(s). Please fix them before using the tool.", fg='red', bold=True))

if __name__ == '__main__':
    cli()
