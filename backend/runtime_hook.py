"""
Runtime hook for PyInstaller to set Playwright browsers path.

This hook runs before the main script and sets the PLAYWRIGHT_BROWSERS_PATH
environment variable to point to the Playwright browsers directory.
"""

import os
import sys
from pathlib import Path

# When running as PyInstaller bundle, sys._MEIPASS contains the extracted files
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    # ✅ FIX: Use system Playwright browsers instead of bundled
    # Playwright browsers are installed at ~/Library/Caches/ms-playwright on macOS
    home = Path.home()

    if sys.platform == 'darwin':
        browsers_path = home / 'Library' / 'Caches' / 'ms-playwright'
    elif sys.platform == 'win32':
        browsers_path = home / 'AppData' / 'Local' / 'ms-playwright'
    else:  # Linux
        browsers_path = home / '.cache' / 'ms-playwright'

    # Only set if browsers exist
    if browsers_path.exists():
        os.environ['PLAYWRIGHT_BROWSERS_PATH'] = str(browsers_path)
        print(f"🎭 Playwright browsers path set to: {browsers_path}")
    else:
        print(f"⚠️  Playwright browsers not found at {browsers_path}")
        print(f"   Please install with: python -m playwright install chromium")
