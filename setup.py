"""
py2app setup script for Monitor Layout Manager
Creates a standalone macOS app bundle.
"""

from setuptools import setup
import py2app
import sys
import os

# App metadata
APP_NAME = "Monitor Layout Manager"
BUNDLE_ID = "com.arturgrochau.monitor-layout-manager"
VERSION = "1.0.0"
COPYRIGHT = "© 2025 Artur Grochau"

# Main app script
APP_SCRIPT = 'app_launcher.py'

# Include all Python files from the project
DATA_FILES = [
    ('', ['requirements.txt', 'README.md']),
    ('cli', ['cli/__init__.py', 'cli/__main__.py', 'cli/advanced_cli.py']),
    ('core', ['core/__init__.py', 'core/display_manager.py', 'core/advanced_display_manager.py']),
    ('gui', ['gui/__init__.py', 'gui/advanced_layout_manager.py', 'gui/display_selector.py', 'gui/settings_dialog.py']),
    ('utils', ['utils/helpers.py']),
    ('scripts', ['scripts/monitor-cli']),
    ('overrides', ['overrides/DisplayVendorID-610/DisplayProductID-31333031.plist']),
]

# py2app options
OPTIONS = {
    'argv_emulation': False,  # Don't emulate command line args
    'no_strip': True,  # Don't strip debug symbols
    'optimize': 0,  # No optimization for better debugging
    'includes': [
        'tkinter',
        'tkinter.ttk',
        'click',
        'rich',
        'colorama',
        'subprocess',
        'json',
        'plistlib',
        're',
        'pathlib',
        'datetime',
        'collections',
    ],
    'excludes': [
        'test',
        'tests',
        'unittest',
    ],
    'packages': [
        'cli',
        'core', 
        'gui',
        'utils',
    ],
    'plist': {
        'CFBundleName': APP_NAME,
        'CFBundleShortVersionString': VERSION,
        'CFBundleVersion': VERSION,
        'CFBundleIdentifier': BUNDLE_ID,
        'CFBundleDisplayName': APP_NAME,
        'CFBundleInfoDictionaryVersion': '6.0',
        'CFBundlePackageType': 'APPL',
        'CFBundleSignature': 'MLM1',
        'CFBundleExecutable': APP_NAME,
        'NSHumanReadableCopyright': COPYRIGHT,
        'NSHighResolutionCapable': True,  # Support Retina displays
        'LSMinimumSystemVersion': '10.15.0',  # macOS Catalina minimum
        'CFBundleDocumentTypes': [],  # No document types
        'LSUIElement': False,  # Show in dock
        'NSRequiresAquaSystemAppearance': False,  # Support dark mode
        'CFBundleIconFile': 'app_icon',  # Icon file
    },
    'iconfile': 'app_icon.icns',  # Path to icon file
}

# Run setup
setup(
    app=[APP_SCRIPT],
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
    name=APP_NAME,
    version=VERSION,
)
