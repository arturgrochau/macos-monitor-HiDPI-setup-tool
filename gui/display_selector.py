# MIT License
# Copyright (c) 2025 Artur Grochau
# 
# This file is part of Monitor Layout Manager.
# See the LICENSE file in the root directory for full license text.

"""
Display Selector Dialog - Monitor configuration and layout setup
Provides interface for selecting display configurations and arrangements
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os

# Ensure import path works
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.display_manager import apply_layout

def run_gui():
    window = tk.Tk()
    window.title("🖥 Monitor Setup Tool")
    window.geometry("300x150")
    window.resizable(False, False)

    # Dropdown
    selected = tk.StringVar()
    dropdown = ttk.Combobox(window, textvariable=selected)
    dropdown['values'] = ("home", "work", "arzopa_only")
    dropdown.current(0)
    dropdown.pack(pady=20)

    # Button
    def on_apply():
        mode = selected.get()
        try:
            apply_layout(mode)
            messagebox.showinfo("Success", f"Layout '{mode}' applied.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    apply_btn = ttk.Button(window, text="Apply Layout", command=on_apply)
    apply_btn.pack()

    window.mainloop()

if __name__ == "__main__":
    run_gui()
