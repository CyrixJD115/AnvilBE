# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for AutoBE
# Enhanced with obfuscation and protection options

block_cipher = None

a = Analysis(
    ['AutoBE.py'],
    pathex=[],
    binaries=[],
    datas=[('locales', 'locales'), ('MUSIC_CREDITS.txt', '.'), ('music', 'music')],
    hiddenimports=[
        'json5',
        'wmi',
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
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,  # Keep as archive for better compatibility
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher,
)

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
    strip=False,  # Strip disabled on Windows (requires MinGW strip utility)
    upx=False,  # UPX disabled to reduce false positives from antivirus software
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='NEXBOX.ico',
    version='version_info.txt',  # Version information for Windows
)
