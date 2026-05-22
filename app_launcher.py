#!/usr/bin/env python3
"""
App launcher for the Monitor Layout Manager macOS bundle.
Handles py2app bundle path setup, validates displayplacer, then starts the GUI.
"""

import sys
import os


def _setup_bundle_paths():
    """Add project subdirectories to sys.path for bundle execution."""
    if getattr(sys, 'frozen', False):
        # py2app: resources are in Contents/Resources
        bundle_root = os.path.normpath(
            os.path.join(os.path.dirname(sys.executable), '..', 'Resources')
        )
    else:
        bundle_root = os.path.dirname(os.path.abspath(__file__))

    for subdir in ('cli', 'core', 'gui', 'utils'):
        path = os.path.join(bundle_root, subdir)
        if os.path.isdir(path) and path not in sys.path:
            sys.path.insert(0, path)

    # Also add the bundle root itself (for version.py, etc.)
    if bundle_root not in sys.path:
        sys.path.insert(0, bundle_root)

    # For py2app, scan lib/python3.x sub-tree as well
    lib_path = os.path.join(bundle_root, '..', 'Frameworks')
    if not os.path.isdir(lib_path):
        lib_path = os.path.join(os.path.dirname(sys.executable), 'lib')
    if os.path.isdir(lib_path):
        for item in os.listdir(lib_path):
            if item.startswith('python'):
                pylib = os.path.join(lib_path, item)
                if pylib not in sys.path:
                    sys.path.insert(0, pylib)
                for subdir in ('cli', 'core', 'gui', 'utils'):
                    p = os.path.join(pylib, subdir)
                    if os.path.isdir(p) and p not in sys.path:
                        sys.path.insert(0, p)


def _check_displayplacer() -> bool:
    """Return True if displayplacer is available; otherwise show an install dialog."""
    try:
        from utils.displayplacer import find_displayplacer
        if find_displayplacer():
            return True
    except Exception:
        pass

    # Fall back to a basic PATH check before showing the dialog
    import subprocess
    try:
        r = subprocess.run(['which', 'displayplacer'], capture_output=True, text=True, timeout=5)
        if r.returncode == 0:
            return True
    except Exception:
        pass

    import tkinter as tk
    from tkinter import messagebox

    root = tk.Tk()
    root.withdraw()

    response = messagebox.askyesno(
        "displayplacer Required",
        "Monitor Layout Manager requires 'displayplacer'.\n\n"
        "Install it now?\n\n"
        "  brew install jakehilborn/jakehilborn/displayplacer\n\n"
        "(This opens a terminal and may take a minute.)"
    )

    if response:
        try:
            result = subprocess.run(
                ['brew', 'install', 'jakehilborn/jakehilborn/displayplacer'],
                timeout=300
            )
            if result.returncode == 0:
                messagebox.showinfo("Installed", "displayplacer installed! Starting app…")
                root.destroy()
                # Clear discovery cache so the new install is found
                try:
                    from utils.displayplacer import invalidate_cache
                    invalidate_cache()
                except Exception:
                    pass
                return True
            else:
                messagebox.showerror("Install Failed",
                                     "Homebrew install failed.\n"
                                     "Run manually:\n"
                                     "  brew install jakehilborn/jakehilborn/displayplacer")
        except subprocess.TimeoutExpired:
            messagebox.showerror("Timeout", "Installation timed out. Try running it manually.")
        except Exception as exc:
            messagebox.showerror("Error", f"Installation failed:\n{exc}")

    root.destroy()
    return False


def main() -> int:
    try:
        _setup_bundle_paths()
    except Exception as exc:
        # If even path setup fails, try to show a basic error dialog
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Startup Error", f"Path setup failed:\n{exc}")
            root.destroy()
        except Exception:
            print(f"Fatal startup error: {exc}", file=sys.stderr)
        return 1

    try:
        if not _check_displayplacer():
            return 1

        from gui.advanced_layout_manager import AdvancedMonitorLayoutManager
        app = AdvancedMonitorLayoutManager()
        app.run()
        return 0

    except ImportError as exc:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Import Error",
            f"Failed to load a required module:\n{exc}\n\n"
            f"sys.path:\n" + "\n".join(sys.path[:5])
        )
        root.destroy()
        return 1

    except Exception as exc:
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Startup Error", f"Unexpected error:\n{exc}")
            root.destroy()
        except Exception:
            print(f"Fatal error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
