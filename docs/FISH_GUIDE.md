# 🐟 Fish Shell Integration Guide

This guide provides fish shell-specific instructions for using the Monitor Layout Manager.

## Quick Start for Fish Users

1. **Install for Fish Shell:**
   ```fish
   ./install-fish.fish
   ```

2. **Launch the GUI:**
   ```fish
   ./gui-fish.fish
   # or
   monitor-layout gui
   # or use alias
   mlgui
   ```

3. **Detect displays:**
   ```fish
   monitor-layout detect
   # or use alias
   mldetect
   ```

## Fish Shell Commands

### Basic Usage
```fish
# Detect connected displays
monitor-layout detect

# Save current layout
monitor-layout save --name "my-setup" --description "My working setup"

# Load a saved layout (interactive)
monitor-layout load

# List all saved layouts
monitor-layout list-layouts

# Launch GUI
monitor-layout gui

# Run diagnostics
monitor-layout doctor
```

### Using Aliases
The installation creates convenient aliases:
```fish
mlt detect          # Short for monitor-layout detect
mlgui               # Launch GUI
mlsave -n work      # Save layout named "work"
mlload              # Interactive load
mllist              # List layouts
mldoctor            # Run diagnostics
```

### Advanced Commands
```fish
# Export layouts to file
monitor-layout export --output my_layouts.json

# Import layouts from file
monitor-layout import-layouts my_layouts.json --merge

# Delete a layout (with confirmation)
monitor-layout delete "old-setup"

# Create backup of current configuration
monitor-layout backup
```

## Fish Shell Features

### Tab Completion
The installation provides intelligent tab completion:
- Command names auto-complete
- Layout names auto-complete for `load` and `delete` commands
- File paths auto-complete for import/export

### Environment Integration
- Automatically detects fish shell and provides fish-optimized output
- Uses fish-style status messages with emojis
- Integrates with fish's command history

### Shell Functions
After installation, you get a `monitor-layout` function that:
- Automatically finds the Python script
- Handles virtual environment activation
- Provides fish-friendly error messages

## Installation Details

The `install-fish.fish` script:
1. Copies fish functions to `~/.config/fish/functions/`
2. Sets up tab completions
3. Installs Python dependencies
4. Installs `displayplacer` via Homebrew (if needed)
5. Adds convenient aliases
6. Tests the installation

## Troubleshooting

### Command Not Found
```fish
# Reload fish configuration
source ~/.config/fish/config.fish

# Or restart fish shell
exec fish
```

### Missing Dependencies
```fish
# Run diagnostics
monitor-layout doctor

# Install Python packages manually
pip3 install click

# Install displayplacer manually
brew install jakehilborn/jakehilborn/displayplacer
```

### GUI Issues
```fish
# Check tkinter availability
python3 -c "import tkinter; print('tkinter OK')"

# Try the simple GUI if advanced fails
python3 gui.py
```

### Permission Issues
```fish
# Make scripts executable
chmod +x install-fish.fish
chmod +x gui-fish.fish
chmod +x monitor-layout

# Fix fish function permissions
chmod +x ~/.config/fish/functions/monitor-layout.fish
```

## Fish Shell Specific Tips

### Using with Fish Abbreviations
```fish
# Add abbreviations for even faster access
abbr --add ml monitor-layout
abbr --add mld monitor-layout detect
abbr --add mlg monitor-layout gui
abbr --add mls monitor-layout save
```

### Integration with Fish Prompt
You can add display status to your fish prompt:
```fish
# In ~/.config/fish/functions/fish_prompt.fish
function fish_prompt
    # ... your existing prompt ...
    
    # Add display count
    set display_count (monitor-layout detect --json-output 2>/dev/null | jq 'length' 2>/dev/null)
    if test -n "$display_count"
        echo -n " 🖥️ $display_count"
    end
    
    # ... rest of prompt ...
end
```

### Fish-Specific Error Handling
The tool provides fish-friendly error messages and exit codes:
```fish
# Check if command succeeded
if monitor-layout detect
    echo "Displays detected successfully!"
else
    echo "Failed to detect displays"
end
```

## Advanced Fish Integration

### Custom Functions
Create your own fish functions in `~/.config/fish/functions/`:

```fish
# ~/.config/fish/functions/switch_to_work.fish
function switch_to_work --description 'Switch to work monitor setup'
    monitor-layout load work
    and echo "✅ Switched to work setup!"
end

# ~/.config/fish/functions/switch_to_home.fish  
function switch_to_home --description 'Switch to home monitor setup'
    monitor-layout load home
    and echo "✅ Switched to home setup!"
end
```

### Keyboard Shortcuts
Add keyboard shortcuts in fish:
```fish
# In ~/.config/fish/config.fish
bind \cw 'switch_to_work'  # Ctrl+W for work setup
bind \ch 'switch_to_home'  # Ctrl+H for home setup
```

## Updating

To update the fish integration:
1. Pull latest changes: `git pull`
2. Re-run installation: `./install-fish.fish`
3. Reload fish: `source ~/.config/fish/config.fish`

---

*This fish integration makes monitor management effortless in the fish shell! 🐟🖥️*
