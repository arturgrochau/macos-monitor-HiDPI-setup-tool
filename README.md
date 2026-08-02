# Monitor Layout Manager

A macOS tool for arranging multiple monitors, saving layout profiles, and getting HiDPI recommendations — with a visual drag-and-drop GUI and a full CLI. Wraps the excellent [displayplacer](https://github.com/jakehilborn/displayplacer) backend.

![macOS](https://img.shields.io/badge/macOS-13%2B-blue)
![Version](https://img.shields.io/badge/version-1.6.0-green)

## What It Does

- **Visual layout editor** — drag monitor boxes to match your physical arrangement, pick resolutions and refresh rates, mark a display as main
- **HiDPI recommendations** — suggests Retina-style scaling where it makes sense
- **Layout profiles** — save named layouts ("Home", "Office", "Presentation") and switch between them instantly
- **CLI** — everything scriptable: detect, save, load, export/import, diagnose

## Requirements

- macOS 13 (Ventura) or later
- [displayplacer](https://github.com/jakehilborn/displayplacer): `brew install jakehilborn/jakehilborn/displayplacer` (the app offers to install it on first launch)
- For running from source: Python 3.12+ and, for the GUI, tkinter (`brew install python-tk`)

## Install

### Option A — Download the app

1. Grab the latest ZIP from [Releases](https://github.com/arturgrochau/macos-monitor-HiDPI-setup-tool/releases/latest) (prebuilt for **Apple Silicon**; on **Intel**, build from source: `git clone` + `./build_app.sh`)
2. Unzip and drag `Monitor Layout Manager.app` to `/Applications`, then double-click it
3. First launch: System Settings › Privacy & Security › **Open Anyway**

### Option B — Run from source

```bash
git clone https://github.com/arturgrochau/macos-monitor-HiDPI-setup-tool.git
cd macos-monitor-HiDPI-setup-tool

./scripts/monitor-layout.sh gui        # launch the GUI
./scripts/monitor-layout.sh cli detect # or use the CLI
```

The script creates a `.venv` and installs dependencies automatically on first run.

## CLI Reference

Run via `./scripts/monitor-layout.sh cli <command>` or `.venv/bin/python -m cli <command>`.

| Command | Description |
|---------|-------------|
| `detect` | Show connected displays (`-d` detailed, `-j` JSON) |
| `save -n NAME [-d DESC]` | Save the current arrangement as a layout |
| `load [NAME]` | Apply a saved layout (`-i` interactive picker) |
| `list-layouts` | List saved layouts with dates |
| `delete NAME` | Delete a saved layout |
| `export [-o FILE]` | Export all layouts to a JSON file |
| `import-layouts FILE [--merge]` | Import layouts from a JSON file |
| `backup` | Snapshot the current live configuration |
| `doctor` | Diagnose setup issues (displayplacer, permissions, tkinter) |
| `gui` | Launch the GUI from the CLI |

## Data Files

| Path | Purpose |
|------|---------|
| `~/.monitor_layouts.json` | Saved layout profiles |
| `~/.monitor_layout_backups/` | Timestamped backups (live-config snapshots and pre-import copies of the layouts file) |

Both are plain JSON — easy to inspect, version, or sync.

## Why displayplacer / Limitations

displayplacer is the best-maintained free display backend for macOS (it works through macOS 26) and uses only public APIs, so it stays stable across OS updates.

The flip side: this tool can set any HiDPI mode **macOS already exposes** for a panel, but it **cannot force HiDPI onto displays macOS denies it** — many 2560x1440 monitors, for example, get no HiDPI modes from macOS at all. If you need to inject custom HiDPI resolutions, you want a paid tool that patches at a lower level, such as [BetterDisplay Pro](https://github.com/waydabber/BetterDisplay) or [SwitchResX](https://www.madrau.com/).

## Uninstall

```bash
# Remove the app (from /Applications, or wherever you unzipped it)
rm -rf "/Applications/Monitor Layout Manager.app"

# Remove data files
rm -f ~/.monitor_layouts.json
rm -rf ~/.monitor_layout_backups

# Optionally remove the backend
brew uninstall displayplacer
```

## Troubleshooting

- **App won't start / crashes:** run `./scripts/monitor-layout.sh cli doctor`
- **displayplacer not found:** `brew install jakehilborn/jakehilborn/displayplacer` (auto-discovered in both `/opt/homebrew/bin` and `/usr/local/bin`)
- **Issues:** [github.com/arturgrochau/macos-monitor-HiDPI-setup-tool/issues](https://github.com/arturgrochau/macos-monitor-HiDPI-setup-tool/issues)

## Development

See [DEVELOPMENT.md](DEVELOPMENT.md) for architecture, building the app bundle, and running tests.

---

*Created by [Artur Grochau](https://github.com/arturgrochau) — Python, Tkinter, MIT licensed*
