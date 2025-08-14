# 🖥️ Monitor Layout Manager - Installation Guide

## 🚀 Standalone App (Recommended)

**The easiest way to use Monitor Layout Manager:**

### 📥 Step 1: Download
- Visit: https://github.com/arturgrochau/monitor-setup-tool/releases
- Download: `Monitor-Layout-Manager-v1.0.0-macOS.zip`

### 📂 Step 2: Extract  
- Double-click the downloaded ZIP file
- macOS will automatically extract it to a folder

### 🖱️ Step 3: Run
- Double-click `Monitor Layout Manager.app`
- **That's it!** The app will launch with the visual interface

## 🔒 First Run Security

When you first run the app, macOS might show security warnings:

### "App cannot be opened" warning:
1. Go to **System Settings** (or System Preferences)
2. Click **Privacy & Security**
3. Find the blocked app and click **"Open Anyway"**
4. Click **"Open"** in the confirmation dialog

### Display permission request:
- The app will ask for permission to control display settings
- Click **"Allow"** to enable monitor layout management

## ✨ Using the App

### Basic Usage:
1. **Arrange**: Drag monitor icons in the visual interface
2. **Save**: Click "Save Layout" and give it a name (e.g., "Work", "Home")
3. **Switch**: Use the dropdown menu to switch between saved layouts
4. **Apply**: Click "Apply" to activate a layout

### Pro Tips:
- **Right-click monitors** for resolution and HiDPI options
- **Save before switching** - create layouts for different scenarios
- **Use descriptive names** - "Morning Coding", "Presentation Mode", etc.
- **Test layouts** - apply and verify before relying on them

## 🛠️ Advanced: Developer Setup

If you want to build from source or contribute:

```bash
git clone https://github.com/arturgrochau/monitor-setup-tool.git
cd monitor-setup-tool
./install.sh                    # Sets up development environment
./build_app.sh                  # Creates standalone .app bundle
```

## 📞 Support

- **Issues**: https://github.com/arturgrochau/monitor-setup-tool/issues
- **Discussions**: https://github.com/arturgrochau/monitor-setup-tool/discussions
- **Documentation**: See README.md in the repository

---

*Created by Artur Grochau*
