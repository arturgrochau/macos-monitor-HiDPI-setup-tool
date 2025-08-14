#!/bin/bash
"""
Create deployment package for Monitor Layout Manager
"""

echo "📦 Creating deployment package..."

# Clean previous builds
rm -rf dist-package
mkdir -p dist-package

# Copy the app bundle
cp -r "dist/Monitor Layout Manager.app" dist-package/

# Create a simple README for users
cat > dist-package/README.txt << 'EOF'
🖥️ Monitor Layout Manager
=========================

A sophisticated macOS monitor layout manager with visual drag-and-drop configuration.

🚀 Quick Start:
1. Double-click "Monitor Layout Manager.app" to launch
2. Use the visual interface to arrange your monitors
3. Save custom layouts with names like "Home", "Work", "Presentation"
4. Switch between layouts instantly

✨ Features:
• Visual drag-and-drop monitor arrangement
• Custom named layouts ("Work", "Home", etc.)
• HiDPI support for Retina displays
• Works with all monitor types and configurations

🔧 Requirements:
• macOS 10.15+ (Catalina or newer)
• External monitor support via displayplacer (auto-installed)

📝 First Run:
• The app will request permission to control your display settings
• Click "Allow" when prompted by macOS security
• If you see a security warning, go to System Settings > Privacy & Security and click "Open Anyway"

💡 Tips:
• Drag monitors in the visual interface to arrange them
• Right-click monitors for resolution and HiDPI options
• Use the dropdown to switch between saved layouts instantly
• Save your current arrangement with descriptive names

🤝 Support:
Created by Artur Grochau
For issues or questions, visit: https://github.com/arturgrochau/monitor-setup-tool

🔐 Privacy:
This app only accesses display settings and saves layout configurations locally.
No data is transmitted or shared externally.
EOF

# Create version info
cat > dist-package/VERSION.txt << EOF
Monitor Layout Manager v1.0.0
Build Date: $(date)
Platform: macOS (Universal)
Created by: Artur Grochau
EOF

# Create the ZIP file
cd dist-package
zip -r "Monitor-Layout-Manager-v1.0.0-macOS.zip" "Monitor Layout Manager.app" README.txt VERSION.txt
cd ..

# Move the ZIP to the main directory
mv "dist-package/Monitor-Layout-Manager-v1.0.0-macOS.zip" ./

echo "✅ Deployment package created: Monitor-Layout-Manager-v1.0.0-macOS.zip"
echo "📁 Size: $(ls -lah Monitor-Layout-Manager-v1.0.0-macOS.zip | awk '{print $5}')"
echo ""
echo "🚀 Ready for distribution!"
echo "   • Upload to GitHub Releases"
echo "   • Users can download, extract, and run the .app directly"
echo "   • No installation or dependencies required"
