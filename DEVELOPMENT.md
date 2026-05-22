# Development Guide

## Prerequisites

| Tool | Install |
|------|---------|
| Python 3.12+ | `brew install python` |
| tkinter | `brew install python-tk` |
| displayplacer | `brew install jakehilborn/jakehilborn/displayplacer` |
| py2app (build only) | `pip install -r requirements-dev.txt` |

## Running from Source

```bash
git clone https://github.com/arturgrochau/monitor-setup-tool.git
cd monitor-setup-tool

# Install runtime dependencies
pip install -r requirements.txt

# Launch GUI (default)
python main.py

# Launch CLI
python main.py --cli detect
python main.py --cli save --name "Work Setup"
python main.py --cli load "Work Setup"
python main.py --cli list-layouts
python main.py --cli doctor      # diagnose setup issues
```

## Project Structure

```
monitor-setup-tool/
├── main.py                          # Entry point: dispatches GUI vs CLI
├── app_launcher.py                  # py2app bundle launcher
├── version.py                       # Single version source of truth
├── setup.py                         # py2app build configuration
├── build_app.sh                     # Build script
├── requirements.txt                 # Runtime dependencies
├── requirements-dev.txt             # Build-only dependencies (py2app)
├── pyproject.toml                   # Modern package metadata
├── core/
│   └── advanced_display_manager.py  # Display detection & layout persistence
├── cli/
│   ├── advanced_cli.py              # Click-based CLI commands
│   └── __main__.py                  # `python -m cli` entry point
├── gui/
│   ├── advanced_layout_manager.py   # Main Tkinter GUI
│   └── settings_dialog.py          # Settings dialog
├── utils/
│   ├── displayplacer.py            # Dynamic displayplacer binary discovery
│   └── helpers.py                  # Shared utility functions
└── overrides/                       # macOS display override plists
```

## Architecture

```
displayplacer list (raw output)
      ↓
AdvancedDisplayManager._parse_display_output()
      ↓
Dict[display_id → Display dataclass]
      ↓
GUI: DraggableDisplay canvas rendering   CLI: formatted table output
      ↓                                         ↓
User arranges / saves as LayoutProfile    apply_layout() → displayplacer cmd
      ↓
~/.monitor_layouts.json (JSON persistence)
```

### Key design decisions

- **Dynamic displayplacer discovery** (`utils/displayplacer.py`): Uses `shutil.which()` first, then falls back to known Homebrew paths. This supports non-standard installs (uv, pyenv, Intel Homebrew).
- **Canvas coordinate system**: Display coordinate `(0, 0)` maps to a fixed canvas pixel `(_CANVAS_ORIGIN_X, canvas_height - _CANVAS_MARGIN_Y)`. All display positions are stored in display-space (pixels), never canvas-space. Scale changes only affect rendering, not stored positions.
- **Layout persistence**: `~/.monitor_layouts.json` — JSON, human-readable, easily backed up.

## Building the .app Bundle

```bash
./build_app.sh
```

Output: `dist/Monitor Layout Manager.app`

Requirements: py2app, Python 3.12+, macOS 13+.

### Versioning

All version strings come from `version.py`:
```python
__version__ = "1.5.0"
```

`setup.py` and `cli/advanced_cli.py` import from this file. When bumping the version, only edit `version.py`.

## Diagnostics

```bash
python main.py --cli doctor
```

Checks: displayplacer path, file permissions, display detection, tkinter availability.

## Contributing

1. Fork the repo and create a feature branch.
2. Run `python main.py` and test the GUI flow end-to-end.
3. Run `python main.py --cli doctor` to verify the CLI is healthy.
4. Open a PR — describe what changed and why.
