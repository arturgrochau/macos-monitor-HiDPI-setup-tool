# 🧠 Copilot Instructions

This project is a **macOS-native monitor layout manager** written in Python.

## 🛠️ Purpose

Build a minimalist, production-ready Python app that:
- Detects all connected monitors (IDs, resolutions, etc.)
- Allows users to create, name, and apply custom monitor "layouts" (e.g., "Home", "Work")
- Uses `displayplacer` under the hood for applying resolutions and arrangements
- Enables HiDPI scaling using `.plist` patches
- Provides an intuitive **Tkinter GUI** for layout creation and switching

## 👤 Use Case

- End-users can select a layout from a dropdown (e.g., "Home", "Cafe") and apply it.
- Layouts define **resolution**, **position**, and **HiDPI state** for each display.
- GUI must reflect macOS-native style (minimalist, clean).
- Tool must work seamlessly across all macOS shells (zsh, fish, etc.)
- Should detect displays dynamically — no hardcoded IDs.
- Optionally save and reuse user-defined layouts.

## 🧰 Stack

- Python 3.11+
- `tkinter` for GUI
- `Click` for optional CLI
- `displayplacer` (installed via Homebrew)
- `plistlib` (Python stdlib) for HiDPI enabling

## 🧩 Components
.
├── main.py               # CLI/GUI unified entrypoint
├── display_manager.py    # Detects displays, applies layouts
├── gui.py                # Tkinter GUI for layout selection & config
├── layout_store.json     # Stores user-defined layouts
├── install.sh            # Installs dependencies + HiDPI patches
├── README.md             # User-facing documentation
└── .github/
└── copilot-instructions.md

## 🔍 Behavior

- On launch, GUI scans displays (`displayplacer list`) and presents dropdown for layout
- Users can define new layouts via GUI (choose display, assign resolution + position)
- Layouts saved in JSON (`layout_store.json`)
- Applying a layout calls `displayplacer` using dynamically generated command
- GUI must show success/error feedback and current active layout

## ✨ Code Guidelines

- Favor pure Python
- Avoid hardcoded UUIDs — detect and store during layout creation
- Provide fallback resolution for displays with limited HiDPI support
- Structure should be modular and extensible
- Prefer `subprocess.run()` over `os.system`
- Use clear docstrings and logging

## 🚀 Out-of-the-box Expectations

- Works after `./install.sh` and `python main.py`
- Creates `.venv` if needed
- Installs `displayplacer`
- Enables required `.plist` overrides for HiDPI
- GUI ready and working on first launch
- Compatible with fish, zsh, bash shells

## 🤖 Claude + Copilot

Please assist with:
- Building native-looking GUI dropdowns for layout and display selection
- Managing JSON layout store
- Reliable parsing of `displayplacer list` output
- Tkinter-based screen detection + preview
- Applying `displayplacer` commands programmatically