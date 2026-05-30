#!/usr/bin/env python3
"""
PyInstaller Build Script for Screenshot Tool Backend

This script bundles the Python FastAPI backend with all dependencies,
including Playwright browsers, into a standalone executable.

Usage:
    python build_backend.py

Output:
    dist/screenshot-backend-{target-triple}
    (e.g., dist/screenshot-backend-aarch64-apple-darwin)
"""

import os
import sys
import platform
import subprocess
import shutil
from pathlib import Path


def get_target_triple():
    """
    Determine the target triple for the current platform.
    
    Returns:
        str: Target triple (e.g., 'aarch64-apple-darwin', 'x86_64-apple-darwin')
    """
    system = platform.system().lower()
    machine = platform.machine().lower()

    if system == 'darwin':
        if machine == 'arm64':
            return 'aarch64-apple-darwin'
        else:
            return 'x86_64-apple-darwin'
    elif system == 'windows':
        if machine in ['amd64', 'x86_64']:
            return 'x86_64-pc-windows-msvc'
        else:
            return 'i686-pc-windows-msvc'
    else:  # Linux
        if machine in ['amd64', 'x86_64']:
            return 'x86_64-unknown-linux-gnu'
        else:
            return 'i686-unknown-linux-gnu'


def get_playwright_browsers_path():
    """
    Get the path where Playwright browsers are installed.
    
    Returns:
        Path: Path to Playwright browsers directory
    """
    # Try to get from environment variable first
    env_path = os.environ.get('PLAYWRIGHT_BROWSERS_PATH')
    if env_path and env_path != '0':
        return Path(env_path)

    # Default locations based on platform
    system = platform.system().lower()
    home = Path.home()

    if system == 'darwin':
        # macOS: ~/Library/Caches/ms-playwright
        return home / 'Library' / 'Caches' / 'ms-playwright'
    elif system == 'windows':
        # Windows: %USERPROFILE%\AppData\Local\ms-playwright
        return home / 'AppData' / 'Local' / 'ms-playwright'
    else:
        # Linux: ~/.cache/ms-playwright
        return home / '.cache' / 'ms-playwright'


def ensure_playwright_browsers():
    """
    Ensure Playwright browsers are installed before bundling.
    """
    print("🔍 Checking Playwright browsers...")

    browsers_path = get_playwright_browsers_path()

    if not browsers_path.exists():
        print(f"📥 Playwright browsers not found at {browsers_path}")
        print("   Installing Playwright browsers (this may take a few minutes)...")

        try:
            # Install only Chromium (we don't need Firefox and WebKit for this tool)
            subprocess.run(
                [sys.executable, "-m", "playwright", "install", "chromium"],
                check=True
            )
            print("✅ Playwright Chromium installed successfully!")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install Playwright browsers: {e}")
            sys.exit(1)
    else:
        print(f"✅ Playwright browsers found at {browsers_path}")

    return browsers_path


def build_with_pyinstaller(target_triple, browsers_path):
    """
    Build the backend using PyInstaller.

    Args:
        target_triple: Target platform triple
        browsers_path: Path to Playwright browsers
    """
    print(f"\n🔨 Building backend for {target_triple}...")

    binary_name = f'screenshot-backend-{target_triple}'

    # PyInstaller arguments
    args = [
        'main.py',
        '--onefile',
        '--name', binary_name,
        '--clean',
        '--noconfirm',

        # ✅ FIX: Don't bundle Chromium binary - it's too complex for PyInstaller
        # We'll copy it manually after the build
        # '--add-data', f'{browsers_path}{os.pathsep}ms-playwright',
        '--add-data', f'requirements.txt{os.pathsep}.',

        # Hidden imports (dependencies that PyInstaller might miss)
        '--hidden-import', 'uvicorn',
        '--hidden-import', 'uvicorn.logging',
        '--hidden-import', 'uvicorn.loops',
        '--hidden-import', 'uvicorn.loops.auto',
        '--hidden-import', 'uvicorn.protocols',
        '--hidden-import', 'uvicorn.protocols.http',
        '--hidden-import', 'uvicorn.protocols.http.auto',
        '--hidden-import', 'uvicorn.protocols.websockets',
        '--hidden-import', 'uvicorn.protocols.websockets.auto',
        '--hidden-import', 'uvicorn.lifespan',
        '--hidden-import', 'uvicorn.lifespan.on',
        '--hidden-import', 'fastapi',
        '--hidden-import', 'playwright',
        '--hidden-import', 'playwright.sync_api',
        '--hidden-import', 'playwright.async_api',
        '--hidden-import', 'pydantic',
        '--hidden-import', 'PIL',
        '--hidden-import', 'imagehash',

        # Collect all submodules
        '--collect-all', 'playwright',
        '--collect-all', 'uvicorn',
        '--collect-all', 'fastapi',

        # Runtime hooks
        '--runtime-hook', 'runtime_hook.py',
    ]

    print(f"   📝 Binary name: {binary_name}")
    print(f"   ⚠️  Note: Chromium will be bundled separately (not via PyInstaller)")

    try:
        import PyInstaller.__main__
        PyInstaller.__main__.run(args)
        print(f"\n✅ Build successful!")
        print(f"   📁 Output: dist/{binary_name}")
    except Exception as e:
        print(f"\n❌ Build failed: {e}")
        sys.exit(1)


def create_runtime_hook():
    """
    Create a runtime hook to set PLAYWRIGHT_BROWSERS_PATH at runtime.

    This ensures Playwright can find the browsers when running
    as a PyInstaller executable.
    """
    hook_content = '''"""
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
'''

    with open('runtime_hook.py', 'w') as f:
        f.write(hook_content)

    print("✅ Created runtime hook")


def copy_to_tauri_binaries(target_triple):
    """
    Copy the built binary to Tauri's binaries directory.
    
    Args:
        target_triple: Target platform triple
    """
    binary_name = f'screenshot-backend-{target_triple}'
    source = Path('dist') / binary_name

    # Tauri expects binaries in frontend/src-tauri/binaries/
    tauri_binaries_dir = Path('../frontend/src-tauri/binaries')
    tauri_binaries_dir.mkdir(parents=True, exist_ok=True)

    dest = tauri_binaries_dir / binary_name

    if source.exists():
        print(f"\n📋 Copying to Tauri binaries directory...")
        shutil.copy2(source, dest)

        # Make executable on Unix-like systems
        if platform.system() != 'Windows':
            os.chmod(dest, 0o755)

        print(f"✅ Copied to: {dest}")
        print(f"   Size: {dest.stat().st_size / (1024 * 1024):.1f} MB")
    else:
        print(f"⚠️  Binary not found at {source}")


def main():
    """Main build process."""
    print("=" * 60)
    print("🚀 Screenshot Tool Backend - PyInstaller Build")
    print("=" * 60)
    print()

    # Step 1: Determine target triple
    target_triple = get_target_triple()
    print(f"🎯 Target platform: {target_triple}")
    print()

    # Step 2: Ensure Playwright browsers are installed
    browsers_path = ensure_playwright_browsers()
    print()

    # Step 3: Create runtime hook
    create_runtime_hook()
    print()

    # Step 4: Build with PyInstaller
    build_with_pyinstaller(target_triple, browsers_path)
    print()

    # Step 5: Copy to Tauri binaries directory
    copy_to_tauri_binaries(target_triple)
    print()

    print("=" * 60)
    print("✅ Build Complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("  1. Test the binary:")
    print(f"     cd dist && ./{f'screenshot-backend-{target_triple}'}")
    print()
    print("  2. Build Tauri app:")
    print("     cd ../frontend && npm run tauri build")
    print()


if __name__ == '__main__':
    main()
