"""
py2app setup script — builds Monitor Layout Manager.app
Run: python setup.py py2app
"""

try:
    from setuptools import setup
    import py2app  # noqa: F401  (ensures py2app hooks are loaded)
except ImportError:
    raise SystemExit(
        "py2app is required to build the app bundle.\n"
        "Install it with:  pip install -r requirements-dev.txt"
    )

import os
import sys

from version import __version__

APP_NAME = "Monitor Layout Manager"
BUNDLE_ID = "com.arturgrochau.monitor-layout-manager"
COPYRIGHT = f"© 2025 Artur Grochau"

APP_SCRIPT = 'app_launcher.py'

DATA_FILES = [
    ('', ['requirements.txt', 'README.md', 'version.py']),
    ('cli', ['cli/__init__.py', 'cli/__main__.py', 'cli/advanced_cli.py']),
    ('core', ['core/__init__.py', 'core/advanced_display_manager.py']),
    ('gui', ['gui/__init__.py', 'gui/advanced_layout_manager.py', 'gui/settings_dialog.py']),
    ('utils', ['utils/__init__.py', 'utils/helpers.py', 'utils/displayplacer.py']),
    ('scripts', ['scripts/monitor-layout.sh']),
]

# Include overrides plist only if it exists
overrides_plist = 'overrides/DisplayVendorID-610/DisplayProductID-31333031.plist'
if os.path.exists(overrides_plist):
    DATA_FILES.append(('overrides/DisplayVendorID-610', [overrides_plist]))

OPTIONS = {
    'argv_emulation': False,
    'no_strip': False,
    'optimize': 1,
    'includes': [
        'tkinter',
        'tkinter.ttk',
        'tkinter.messagebox',
        'tkinter.simpledialog',
        'tkinter.filedialog',
        'tkinter.font',
        'click',
        'rich',
        'colorama',
        'subprocess',
        'json',
        're',
        'pathlib',
        'datetime',
        'dataclasses',
        'shutil',
    ],
    'excludes': [
        'test',
        'tests',
        'unittest',
        'doctest',
        'pdb',
        'pydoc',
    ],
    'packages': [
        'tkinter',
        'cli',
        'core',
        'gui',
        'utils',
    ],
    'plist': {
        'CFBundleName': APP_NAME,
        'CFBundleShortVersionString': __version__,
        'CFBundleVersion': __version__,
        'CFBundleIdentifier': BUNDLE_ID,
        'CFBundleDisplayName': APP_NAME,
        'CFBundleInfoDictionaryVersion': '6.0',
        'CFBundlePackageType': 'APPL',
        'CFBundleSignature': 'MLM1',
        'CFBundleExecutable': APP_NAME,
        'NSHumanReadableCopyright': COPYRIGHT,
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '13.0',   # Ventura+ (drops legacy 10.15)
        'CFBundleDocumentTypes': [],
        'LSUIElement': False,
        'NSRequiresAquaSystemAppearance': False,
        'CFBundleIconFile': 'app_icon',
    },
    'iconfile': 'app_icon.icns',
}

setup(
    app=[APP_SCRIPT],
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
    name=APP_NAME,
    version=__version__,
)
