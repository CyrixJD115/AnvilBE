# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for AutoBE - Linux (onefile, mirrors Windows build)

import os
from pathlib import Path

ROOT = Path(SPECPATH)

block_cipher = None

a = Analysis(
    [str(ROOT / 'AutoBE.py')],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        (str(ROOT / 'locales'),         'locales'),
        (str(ROOT / 'MUSIC_CREDITS.txt'), '.'),
        (str(ROOT / 'music'),           'music'),
    ],
    hiddenimports=[
        'json5',
        'pypresence',
        'pypresence.presence',
        'aiohttp',
        'multidict',
        'yarl',
        'async_timeout',
        'requests',
        'tkinter',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'tkinter.scrolledtext',
        'tkinter.ttk',
        'tkinter.simpledialog',
        'tkinter.font',
        'urllib.request',
        'urllib.parse',
        'hashlib',
        'uuid',
        'zipfile',
        'tempfile',
        'threading',
        'collections',
        'base64',
        'csv',
        'io',
        'math',
        'traceback',
        'logging',
        're',
        'platform',
        'subprocess',
        'datetime',
        'ctypes',
        'shutil',
        'os',
        'sys',
        'pygame',
        'pygame.mixer',
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
        # wmi is Windows-only — excluded on Linux
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'pytest',
        'unittest',
        'wmi',           # Windows-only
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='AutoBE',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # No icon on Linux — set via .desktop file
)
