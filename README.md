# 🖥️ Monitor Layout Manager

[![macOS](https://img.shields.io/badge/macOS-10.15+-blue.svg)](https://www.apple.com/macos/)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Downloads](https://img.shields.io/github/downloads/arturgrochau/monitor-setup-tool/total.svg)](https://github.com/arturgrochau/monitor-setup-tool/releases)

**The simplest way to manage your Mac's monitor layouts. Drag, drop, save, apply.**

<p align="center">
  <a href="https://github.com/arturgrochau/monitor-setup-tool/releases/download/v1.0.0/monitor-layout-manager-v1.0.0-minimal.zip">
    <img src="https://img.shields.io/badge/Download-Latest%20Release-brightgreen?style=for-the-badge&logo=download" alt="Download Latest Release">
  </a>
</p>

## 🚀 Get Started in 30 Seconds

1. **[Download ZIP](https://github.com/arturgrochau/monitor-setup-tool/releases/download/v1.0.0/monitor-layout-manager-v1.0.0-minimal.zip)**
2. **Unzip** and double-click **`Monitor Layout Manager`**
3. **Done!** 🎉

> **Just want to try it?** Double-click the `Monitor Layout Manager` file after download. It handles everything automatically.

## ✨ What It Does

🖱️ **Drag & drop** monitors to arrange them  
💾 **Save layouts** like "Home", "Office", "Presentation"  
⚡ **One-click switching** between saved layouts  
🔄 **Auto-detects** all connected displays  
⚙️ **HiDPI scaling** and resolution control  

## 

![GUI Preview](docs/assets/Advanced_Monitor_Layout_Manager.png)

## 🔧 System Requirements

- macOS 10.15+ (Catalina or newer)
- Python 3.8+ (usually pre-installed)
- Any monitor setup (USB-C, HDMI, DisplayPort, etc.)

## 🆘 Need Help?

**🔧 Not working?** Run `./install.sh` in terminal first  
**📚 Want more?** Check the [Complete Guide](docs/README_detailed.md)  
**🐠 Fish user?** See [Fish Integration](docs/FISH_GUIDE.md)  

---

## 🔌 Advanced: Command Line Interface

<details>
<summary>For developers and automation enthusiasts</summary>

### Quick CLI Commands
```bash
# Launch GUI (same as double-clicking)
./monitor-layout

# CLI mode  
./monitor-layout --cli detect        # Show all monitors
./monitor-layout --cli save "Work"   # Save current as "Work" 
./monitor-layout --cli load "Work"   # Apply "Work" layout
./monitor-layout --cli list-layouts  # Show all saved layouts
```

### Full CLI Reference
```bash
# Display management
./monitor-layout --cli detect                    # Detect displays
./monitor-layout --cli doctor                    # System diagnostics

# Layout operations  
./monitor-layout --cli save -n "Name" -d "Desc"  # Save with description
./monitor-layout --cli load "Layout Name"        # Apply saved layout
./monitor-layout --cli delete "Layout Name"      # Remove layout
./monitor-layout --cli list-layouts             # List all layouts

# Backup & sharing
./monitor-layout --cli backup                   # Create backup
./monitor-layout --cli export layouts.json     # Export all layouts  
./monitor-layout --cli import layouts.json     # Import layouts
```

</details>

---

<div align="center">

**Created by [Artur Grochau](https://github.com/arturgrochau)**

</div>
