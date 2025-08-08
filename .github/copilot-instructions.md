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

- End-users select a layout from a dropdown (e.g., "Home", "Cafe") and apply it.
- Layouts define **resolution**, **position**, and **HiDPI state** per display.
- GUI must reflect macOS-native style (minimalist, clean).
- Should work seamlessly across all macOS shells (zsh, fish, bash).
- Dynamically detects displays — no hardcoded IDs.

## 🧰 Stack

- Python 3.11+
- `tkinter` + `ttk` for GUI
- `Click` for CLI
- `displayplacer` (installed via Homebrew)
- `plistlib` for HiDPI support

## 🧩 Structure

.
├── main.py                  # Unified CLI/GUI launcher
├── core/                    # Display logic + layout application
├── gui/                     # Tkinter GUI
├── cli/                     # CLI definitions (click)
├── utils/                   # Helper utilities
├── scripts/                 # Shell wrappers + fish support
├── overrides/              # HiDPI plist patches
├── install.sh              # Setup script
├── README.md               # Docs
└── .github/copilot-instructions.md

## 🔍 Behavior

- On launch, GUI scans displays (`displayplacer list`)
- Users can define new layouts, select resolutions/positions/HiDPI
- Layouts saved in `.monitor-layout/`
- Applying a layout calls `displayplacer` dynamically
- GUI shows current layout, errors, and logs
- Auto-creates `.venv` on first run
- Shows branding: “Created by Artur Grochau”

## 🚀 Out-of-the-box UX

```bash
git clone https://github.com/arturgrochau/monitor-setup-tool.git
cd monitor-setup-tool
./install.sh

# GUI
python3 main.py

# CLI
python3 main.py --cli
Works in: fish, zsh, bash. No config required.

🤖 Claude / Copilot Tasks
	•	Parse displayplacer list into structured data
	•	Build GUI with ttk for dropdowns / layout preview
	•	Enable smart display positioning
	•	Detect active shell silently
	•	Minimal install + run UX, no user setup required
	•	**ALWAYS log dev actions in docs/DEVELOPMENT_LOG.md using format: [YYYY-MM-DD HH:MM:SS] ACTION: <summary>**