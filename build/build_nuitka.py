#!/usr/bin/env python3
"""
Build Anvil-MC as a single-file executable via Nuitka.

Usage:
    python build/build_nuitka.py                   # auto-detect OS
    python build/build_nuitka.py --windows          # force Windows build
    python build/build_nuitka.py --linux            # force Linux build
    python build/build_nuitka.py --macos            # force macOS build
    python build/build_nuitka.py --clean            # clean build artifacts first
    python build/build_nuitka.py --version 7.0.3    # override version number

Requirements:
    pip install nuitka
    (Linux) sudo apt install ccache python3-dev patchelf
    (Windows) install MSVC or MinGW
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP_NAME = "Anvil-MC"
MAIN_SCRIPT = ROOT / "main.py"
DIST_DIR = ROOT / "dist"
BUILD_DIR = ROOT / "build" / "nuitka-work"

# Read version from version.yaml
_version_file = ROOT / "version.yaml"
_match = re.search(r'^version:\s*(.+)$', _version_file.read_text("utf-8"), re.MULTILINE)
VERSION = _match.group(1).strip().strip('"\'') if _match else "0.0.0"
# Strip non-numeric suffix for Nuitka's --file-version (needs pure numeric)
_VERSION_NUMERIC = re.sub(r'(\s+|-)[a-zA-Z].*', '', VERSION).strip() or VERSION


def clean():
    for d in [DIST_DIR, BUILD_DIR]:
        if d.exists():
            shutil.rmtree(d)
            print(f"Removed {d}")


def build_windows():
    out = DIST_DIR / "windows"
    cmd = [
        sys.executable, "-m", "nuitka",
        "--onefile",
        f"--output-dir={out}",
        f"--output-filename={APP_NAME}.exe",
        f"--product-name={APP_NAME}",
        f"--file-version={_VERSION_NUMERIC}",
        f"--file-description=Minecraft Bedrock Edition Addon Merger",
        "--enable-plugin=pyside6",
        f"--include-data-dir=resources=resources",
        f"--include-data-dir=locales=locales",
        f"--include-data-dir=src/theme=src/theme",
        "--include-package=src",
        f"--windows-icon-from-ico={ROOT / 'src' / 'theme' / 'anvil.ico'}",
        "--windows-console-mode=disable",
        "--assume-yes-for-downloads",
        "--noinclude-pytest-mode=nofollow",
        "--noinclude-default-mode=error",
        str(MAIN_SCRIPT),
    ]
    print("Running Nuitka (Windows)...")
    subprocess.check_call(cmd, cwd=ROOT)
    print(f"Executable created at {out / f'{APP_NAME}.exe'}")


def build_linux():
    out = DIST_DIR / "linux"
    cmd = [
        sys.executable, "-m", "nuitka",
        "--onefile",
        f"--output-dir={out}",
        f"--output-filename={APP_NAME}",
        f"--product-name={APP_NAME}",
        f"--file-version={_VERSION_NUMERIC}",
        "--enable-plugin=pyside6",
        f"--include-data-dir=resources=resources",
        f"--include-data-dir=locales=locales",
        f"--include-data-dir=src/theme=src/theme",
        "--include-package=src",
        "--assume-yes-for-downloads",
        "--noinclude-pytest-mode=nofollow",
        "--noinclude-default-mode=error",
        str(MAIN_SCRIPT),
    ]
    print("Running Nuitka (Linux)...")
    subprocess.check_call(cmd, cwd=ROOT)
    print(f"Executable created at {out / APP_NAME}")


def build_macos():
    out = DIST_DIR / "macos"

    # Convert .ico to .png for macOS app icon
    icon_png = ROOT / "src" / "theme" / "anvil.png"
    if not icon_png.exists():
        from PIL import Image
        img = Image.open(ROOT / "src" / "theme" / "anvil.ico")
        img.save(icon_png, format="PNG")
    # Ensure imageio is available for Nuitka's PNG->ICNS conversion
    try:
        import imageio  # noqa: F401
    except ImportError:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "imageio"],
            cwd=ROOT,
        )

    cmd = [
        sys.executable, "-m", "nuitka",
        "--standalone",
        "--macos-create-app-bundle",
        f"--macos-app-icon={icon_png}",
        f"--output-dir={out}",
        f"--output-filename={APP_NAME}",
        f"--product-name={APP_NAME}",
        f"--file-version={_VERSION_NUMERIC}",
        "--enable-plugin=pyside6",
        f"--include-data-dir=resources=resources",
        f"--include-data-dir=locales=locales",
        f"--include-data-dir=src/theme=src/theme",
        "--include-package=src",
        "--macos-target-arch=arm64",
        "--assume-yes-for-downloads",
        "--noinclude-pytest-mode=nofollow",
        "--noinclude-default-mode=error",
        str(MAIN_SCRIPT),
    ]
    print("Running Nuitka (macOS)...")
    subprocess.check_call(cmd, cwd=ROOT)
    # Nuitka names the .app after the main script (main.app); rename to APP_NAME
    app_bundle = out / f"{APP_NAME}.app"
    default_bundle = out / "main.app"
    if default_bundle.exists() and not app_bundle.exists():
        default_bundle.rename(app_bundle)
    # List output for debugging
    for p in sorted(out.iterdir()):
        print(f"  {p.name}")
    print(f"App bundle created at {app_bundle}")


def parse_args():
    parser = argparse.ArgumentParser(description="Build Anvil-MC with Nuitka")
    parser.add_argument("--windows", action="store_true", help="Build for Windows")
    parser.add_argument("--linux", action="store_true", help="Build for Linux")
    parser.add_argument("--macos", action="store_true", help="Build for macOS")
    parser.add_argument("--clean", action="store_true", help="Remove previous build artifacts")
    parser.add_argument("--version", default=None, help="Override version number")
    return parser.parse_args()


def main():
    args = parse_args()

    global VERSION, _VERSION_NUMERIC
    if args.version:
        VERSION = args.version
        _VERSION_NUMERIC = re.sub(r'[a-zA-Z]+[0-9]*', '', VERSION).rstrip('.') or VERSION

    if args.clean:
        clean()
        if not (args.windows or args.linux):
            return

    if args.windows:
        build_windows()
    elif args.linux:
        build_linux()
    elif args.macos:
        build_macos()
    elif sys.platform == "win32":
        build_windows()
    elif sys.platform == "darwin":
        build_macos()
    else:
        build_linux()


if __name__ == "__main__":
    main()
