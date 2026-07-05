import os as _os
import zipfile as _zipfile
import json as _json
import random as _random
import shutil as _shutil
import ctypes as _ctypes
import tkinter as _tk
from tkinter import filedialog as _filedialog, messagebox as _messagebox, scrolledtext as _scrolledtext, Menu as _Menu, ttk as _ttk, simpledialog as _simpledialog, font as _font
import uuid as _uuid
import hashlib
import platform
try:
    import winreg as _winreg
except Exception:
    _winreg = None
import datetime as _datetime
import subprocess
import re as _re
import logging as _logging
import urllib.request as _request
try:
    import psutil
except ImportError:
    psutil = None
import tempfile as _tempfile
import requests as _requests
import base64
import json5
import sys
import traceback
import logging
import math
import csv
import io
import pathlib as _pathlib
try:
    import extendedbe as _extendedbe
    _EXTENDEDBE_FIXERS = _extendedbe.load_fixers()
    if _EXTENDEDBE_FIXERS:
        _logging.info(f"[ExtendedBE] Loaded {len(_EXTENDEDBE_FIXERS)} addon fixer(s): "
                      + ", ".join(getattr(m, 'DESCRIPTION', m.__name__) for m in _EXTENDEDBE_FIXERS))
    # Import universal compatibility patcher
    from extendedbe.universal_compatibility import UniversalCompatibilityPatcher
    _UNIVERSAL_PATCHER = UniversalCompatibilityPatcher()
except Exception:
    _extendedbe = None
    _EXTENDEDBE_FIXERS = []
    _UNIVERSAL_PATCHER = None

# Import Excel manager from extendedbe
try:
    from extendedbe.excel_manager import ExcelManager, is_excel_available
    _EXCEL_AVAILABLE = is_excel_available()
    if _EXCEL_AVAILABLE:
        _logging.info("[Excel Manager] Excel functionality available")
        _EXCEL_MANAGER = ExcelManager()
    else:
        _EXCEL_MANAGER = None
except Exception:
    _EXCEL_AVAILABLE = False
    _EXCEL_MANAGER = None
import threading
import time as _time
from collections import defaultdict
import webbrowser
try:
    from PIL import Image as _PILImage
    _PIL_AVAILABLE = True
except ImportError:
    _PILImage = None
    _PIL_AVAILABLE = False

# On Windows when run as .py with Python 3.14+: re-launch with 3.13 only (pygame/deps work there). Never use current exe's pythonw when on 3.14 (that would run 3.14 and crash).
try:
    if not getattr(sys, "frozen", False) and platform.system() == "Windows" and sys.version_info >= (3, 14):
        _script = _os.path.abspath(__file__)
        _cwd = _os.path.dirname(_script)
        _flags = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
        # Get 3.13's pythonw so we run with 3.13 (not 3.14)
        _p = subprocess.run(
            ["py", "-3.13", "-c", "import sys, os; print(os.path.join(os.path.dirname(sys.executable), 'pythonw.exe'))"],
            capture_output=True, text=True, timeout=5, creationflags=_flags, cwd=_cwd
        )
        if _p.returncode == 0 and _p.stdout:
            _pyw = _p.stdout.strip().strip('"')
            if _os.path.isfile(_pyw):
                subprocess.Popen([_pyw, _script] + sys.argv[1:], cwd=_cwd, creationflags=_flags)
                sys.exit(0)
        # Fallback: run with py -3.13 (may show CMD briefly; app will hide it)
        subprocess.Popen(["py", "-3.13", _script] + sys.argv[1:], cwd=_cwd, creationflags=_flags)
        sys.exit(0)
except Exception:
    pass

def _hide_console_window():
    """Hide the CMD/console window on Windows when running as .py (no effect when frozen). Only hides; no FreeConsole to avoid crashes."""
    if getattr(sys, "frozen", False) or platform.system() != "Windows":
        return
    try:
        _h = _ctypes.windll.kernel32.GetConsoleWindow()
        if _h:
            _ctypes.windll.user32.ShowWindow(_h, 0)  # SW_HIDE
    except Exception:
        pass

_hide_console_window()

# PIL/Pillow for reliable pack icon loading (some PNGs fail with Tk's native PhotoImage on Windows)
_PIL_AVAILABLE = False
_PIL_Image = None
_PIL_ImageTk = None
try:
    from PIL import Image as _PIL_Image
    from PIL import ImageTk as _PIL_ImageTk
    _PIL_AVAILABLE = _PIL_Image is not None and _PIL_ImageTk is not None
except (ImportError, AttributeError, Exception):
    pass

# Discord Rich Presence (optional - gracefully handles if not installed)
DISCORD_RPC_AVAILABLE = False
Presence = None
try:
    from pypresence import Presence  # type: ignore
    DISCORD_RPC_AVAILABLE = Presence is not None
except (ImportError, AttributeError, Exception):
    DISCORD_RPC_AVAILABLE = False
    Presence = None

# Write logs to %APPDATA%\AutoBE\ so the app works without admin rights
# when installed under C:\Program Files (x86)\
# Try multiple locations in order so there is always somewhere writable.
_LOG_PATH = ""
for _log_candidate_dir in [
    _os.path.join(_os.environ.get("APPDATA", ""), "AutoBE"),
    _os.path.join(_os.path.expanduser("~"), "Desktop", "AutoBE"),
    _os.path.join(_os.path.expanduser("~"), "AutoBE"),
    _os.path.dirname(_os.path.abspath(__file__)),
]:
    if not _log_candidate_dir:
        continue
    try:
        _os.makedirs(_log_candidate_dir, exist_ok=True)
        _test_path = _os.path.join(_log_candidate_dir, "error_log.txt")
        with open(_test_path, "a", encoding="utf-8") as _tf:
            pass  # just verify the path is writable
        _LOG_DIR = _log_candidate_dir
        _LOG_PATH = _test_path
        break
    except Exception:
        continue

try:
    import logging.handlers as _log_handlers
    _root_logger = logging.getLogger()
    _root_logger.setLevel(logging.DEBUG)
    _log_fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    _file_handler = _log_handlers.RotatingFileHandler(
        _LOG_PATH, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8")
    _file_handler.setLevel(logging.DEBUG)
    _file_handler.setFormatter(_log_fmt)
    _root_logger.addHandler(_file_handler)
    # Also print WARNING+ to console so non-frozen dev runs show issues immediately
    _con_handler = logging.StreamHandler()
    _con_handler.setLevel(logging.WARNING)
    _con_handler.setFormatter(_log_fmt)
    _root_logger.addHandler(_con_handler)
    # Silence third-party library loggers so they don't flood the log
    for _noisy_lib in ('PIL', 'PIL.PngImagePlugin', 'PIL.TiffImagePlugin',
                       'urllib3', 'urllib3.connectionpool', 'requests',
                       'asyncio', 'pypresence'):
        logging.getLogger(_noisy_lib).setLevel(logging.WARNING)
    # Force-write and flush immediately so the file appears on disk at launch
    _logging.info(f"AutoBE started — log: {_LOG_PATH}")
    _file_handler.flush()
except Exception as _log_setup_err:
    try:
        with open(_LOG_PATH or "error_log.txt", "a", encoding="utf-8") as _lf:
            _lf.write(f"[LOGGING SETUP FAILED] {_log_setup_err}\n")
    except Exception:
        pass

# --- Translation (i18n) ---
_BASE_DIR = _os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else _os.path.dirname(_os.path.abspath(__file__))
# When frozen, locale files are in the extracted bundle (sys._MEIPASS)
_LOCALE_DIR = _os.path.join(getattr(sys, '_MEIPASS', _BASE_DIR), "locales")
# Music: when frozen, look in bundle first then next to exe; when run from source, next to script
_MEIPASS = getattr(sys, '_MEIPASS', None)
_MUSIC_DIR = _os.path.join(_BASE_DIR, "music")  # used when not frozen
# Vendor folder (required for users)
_VENDOR_DIR = _os.path.join(_BASE_DIR, "vendor") if _os.path.isdir(_os.path.join(_BASE_DIR, "vendor")) else _os.path.join(getattr(sys, '_MEIPASS', _BASE_DIR), "vendor")
_MUSIC_DIRS = (
    [_os.path.join(_MEIPASS, "music"), _os.path.join(_BASE_DIR, "music")] if _MEIPASS
    else [_os.path.join(_BASE_DIR, "music")]
)
_TRANSLATIONS = {}
_APP_ICON_IMAGE_REF = None

def _get_app_icon_paths():
    """Return candidate icon paths in priority order."""
    roots = []
    try:
        roots.append(getattr(sys, "_MEIPASS", ""))
    except Exception:
        pass
    roots.append(_BASE_DIR)
    roots.append(_os.path.dirname(_os.path.abspath(__file__)))
    candidates = []
    seen = set()
    for r in roots:
        if not r:
            continue
        for name in ("NEXBOX.ico", "NEXBOX.png", "icon.ico", "icon.png"):
            p = _os.path.join(r, name)
            if p not in seen:
                seen.add(p)
                candidates.append(p)
    return candidates

def _get_titlebar_icon_image(size=14):
    """Load a small icon image for custom drawn title bars."""
    for icon_path in _get_app_icon_paths():
        if not _os.path.isfile(icon_path):
            continue
        try:
            if _PIL_AVAILABLE and _PIL_Image is not None and _PIL_ImageTk is not None:
                _img = _PIL_Image.open(icon_path).convert("RGBA")
                _resample = getattr(_PIL_Image.Resampling, "LANCZOS", None) or getattr(_PIL_Image, "LANCZOS", 1)
                _img = _img.resize((size, size), _resample)
                return _PIL_ImageTk.PhotoImage(_img)
        except Exception:
            pass
        try:
            _img = _tk.PhotoImage(file=icon_path)
            try:
                _w = max(1, int(_img.width()))
                _h = max(1, int(_img.height()))
                _factor = max(1, _w // size, _h // size)
                if _factor > 1:
                    _img = _img.subsample(_factor, _factor)
            except Exception:
                pass
            return _img
        except Exception:
            continue
    return None

def _set_app_user_model_id():
    """Register a unique AppUserModelID so Windows gives AutoBE its own
    taskbar button instead of grouping it under the generic Python slot."""
    try:
        _ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "CodeNex.AutoBE.1")
    except Exception:
        pass

def _force_taskbar_button(window):
    """overrideredirect(True) strips the taskbar button on Windows.
    Add WS_EX_APPWINDOW to the extended window style to force it back,
    then briefly withdraw/deiconify so the taskbar refreshes the entry."""
    try:
        GWL_EXSTYLE    = -20
        WS_EX_APPWINDOW  = 0x00040000
        WS_EX_TOOLWINDOW = 0x00000080
        user32 = _ctypes.windll.user32
        window.update_idletasks()
        hwnd = int(window.winfo_id())
        style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        style = (style | WS_EX_APPWINDOW) & ~WS_EX_TOOLWINDOW
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
        # Re-map the window so Windows picks up the new style and icon
        window.withdraw()
        window.after(50, window.deiconify)
    except Exception:
        pass

def _set_win32_icon(hwnd, ico_path):
    """Push an .ico file into a window's taskbar button via WM_SETICON.
    winfo_id() returns the client-area HWND; the taskbar slot belongs to the
    top-level frame, so walk up via GetParent first."""
    try:
        LR_LOADFROMFILE = 0x00000010
        IMAGE_ICON = 1
        WM_SETICON = 0x0080
        ICON_SMALL, ICON_BIG = 0, 1
        SM_CXICON = 11
        user32 = _ctypes.windll.user32
        # Walk up to the real top-level frame (parent of the Tk client window)
        parent = user32.GetParent(hwnd)
        if parent:
            hwnd = parent
        # Load large icon (32x32 or system default)
        hicon_big = user32.LoadImageW(
            None, ico_path, IMAGE_ICON,
            user32.GetSystemMetrics(SM_CXICON),
            user32.GetSystemMetrics(SM_CXICON),
            LR_LOADFROMFILE)
        # Load small icon (16x16)
        hicon_small = user32.LoadImageW(
            None, ico_path, IMAGE_ICON, 16, 16, LR_LOADFROMFILE)
        if hicon_big:
            user32.SendMessageW(_ctypes.c_void_p(hwnd), WM_SETICON, ICON_BIG,
                                _ctypes.c_void_p(hicon_big))
        if hicon_small:
            user32.SendMessageW(_ctypes.c_void_p(hwnd), WM_SETICON, ICON_SMALL,
                                _ctypes.c_void_p(hicon_small))
    except Exception:
        pass

def _apply_window_icon_global(window):
    """Apply branded app icon to any Tk/Toplevel window."""
    global _APP_ICON_IMAGE_REF
    try:
        if not window or not window.winfo_exists():
            return
        _apply_dark_title_bar(window)
        try:
            # Re-apply once the native window is fully mapped.
            window.after(60, lambda w=window: _apply_dark_title_bar(w))
            window.after(220, lambda w=window: _apply_dark_title_bar(w))
            # Re-apply whenever Windows re-themes/re-focuses the window.
            window.bind("<Map>", lambda e, w=window: _apply_dark_title_bar(w), add="+")
            window.bind("<FocusIn>", lambda e, w=window: _apply_dark_title_bar(w), add="+")
        except Exception:
            pass
        for icon_path in _get_app_icon_paths():
            if not _os.path.isfile(icon_path):
                continue
            lower = icon_path.lower()
            if lower.endswith(".ico"):
                try:
                    window.iconbitmap(icon_path)
                except Exception:
                    pass
                # Also push via Win32 so the taskbar button gets the icon
                try:
                    window.update_idletasks()
                    hwnd = int(window.winfo_id())
                    _set_win32_icon(hwnd, icon_path)
                    # Re-apply after window is fully mapped (taskbar slot may not exist yet)
                    window.after(300, lambda h=hwnd, p=icon_path: _set_win32_icon(h, p))
                except Exception:
                    pass
                return
            try:
                img = _tk.PhotoImage(file=icon_path)
                _APP_ICON_IMAGE_REF = img  # keep reference to avoid GC
                window.iconphoto(True, img)
                return
            except Exception:
                continue
    except Exception:
        pass

def _apply_dark_title_bar(window):
    """Use Windows DWM dark title bar for Tk windows when available."""
    if platform.system() != "Windows":
        return
    try:
        window.update_idletasks()
        hwnd = int(window.winfo_id())
    except Exception:
        return
    try:
        _dwm = _ctypes.windll.dwmapi
        val = _ctypes.c_int(1)
        # Windows 10/11 use 20, older builds may use 19.
        for attr in (20, 19):
            try:
                _dwm.DwmSetWindowAttribute(
                    _ctypes.c_void_p(hwnd),
                    _ctypes.c_int(attr),
                    _ctypes.byref(val),
                    _ctypes.sizeof(val),
                )
            except Exception:
                pass
        # Force caption/text colors so it stays dark even on light system theme.
        # DWM expects COLORREF (0x00bbggrr). Black=0x000000, white=0xFFFFFF.
        try:
            caption_color = _ctypes.c_int(0x000000)   # black
            text_color = _ctypes.c_int(0xFFFFFF)      # white
            _dwm.DwmSetWindowAttribute(
                _ctypes.c_void_p(hwnd),
                _ctypes.c_int(35),  # DWMWA_CAPTION_COLOR
                _ctypes.byref(caption_color),
                _ctypes.sizeof(caption_color),
            )
            _dwm.DwmSetWindowAttribute(
                _ctypes.c_void_p(hwnd),
                _ctypes.c_int(36),  # DWMWA_TEXT_COLOR
                _ctypes.byref(text_color),
                _ctypes.sizeof(text_color),
            )
        except Exception:
            pass
    except Exception:
        pass
# Optional: background music (pygame.mixer). Hide pygame startup message in console.
_PYGAME_MIXER_AVAILABLE = False
_pygame = None
try:
    _os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    if platform.system() == "Windows":
        _os.environ.setdefault("SDL_AUDIODRIVER", "directsound")
    import pygame as _pygame  # type: ignore[import-untyped]
    _PYGAME_MIXER_AVAILABLE = _pygame is not None
except Exception:
    _pygame = None
_CURRENT_LANG = "en"

def _tr_load(lang):
    """Load locale JSON into _TRANSLATIONS. Fallback to en if missing."""
    global _CURRENT_LANG
    _CURRENT_LANG = (lang or "en").lower()
    path = _os.path.join(_LOCALE_DIR, _CURRENT_LANG + ".json")
    try:
        with open(path, 'r', encoding='utf-8') as f:
            _TRANSLATIONS.clear()
            _TRANSLATIONS.update(_json.load(f))
    except Exception:
        if (lang or "").lower() != "en":
            _tr_load("en")

def _(key):
    """Return translation for key, or key itself if not found."""
    return _TRANSLATIONS.get(key, key)

def _f(key, **kwargs):
    """Return translation for key with placeholders filled (e.g. {version} -> version=...)."""
    return _(key).format(**kwargs)


def _parse_lang_kv(text):
    out = {}
    try:
        for line in text.splitlines():
            if not line:
                continue
            s = line.strip()
            if not s or s.startswith('#'):
                continue
            if '=' not in s:
                continue
            k, v = s.split('=', 1)
            k = k.strip()
            if not k:
                continue
            out[k] = v.strip()
    except Exception:
        pass
    return out

def _get_tos_text():
    """Load TOS text from locales/tos_{lang}.txt. Falls back to tos_en.txt."""
    for lang in (_CURRENT_LANG, "en"):
        path = _os.path.join(_LOCALE_DIR, "tos_" + lang + ".txt")
        if _os.path.isfile(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception:
                pass
    return ""

def _init_translations():
    """Load language from settings and apply. Call early so UI uses it."""
    try:
        # Settings are stored next to the exe (or in script dir when not frozen)
        settings_path = _os.path.join(_BASE_DIR, ".autobe", "settings.be")
        if _os.path.exists(settings_path):
            with open(settings_path, 'r', encoding='utf-8') as f:
                lang = _json.load(f).get("lang", "en")
        else:
            lang = "en"
        _tr_load(lang or "en")
    except Exception:
        _tr_load("en")

# GitHub token for API (version.txt, blacklist.txt, keys.csv, hwid) — from AutoBE 7.5
GITHUB_TOKEN = os.environ.get("AUTOBE_GITHUB_TOKEN", "")
# App version: bump this and version_info.txt when you release.
# version.txt on GitHub: line 1 = minimum allowed to run, line 2 = latest version for "Check for updates".
APP_VERSION = "7.0.2.0"
GITHUB_REPO = os.environ.get("AUTOBE_GITHUB_REPO", "FrostyHostMC/AutoBE")
# How often to re-check for updates in the background (ms). First check is 6s after unlock; then every this interval.
UPDATE_CHECK_INTERVAL_MS = 30 * 60 * 1000  # 30 minutes

def log_error(e):
    """Log errors without injecting fake traceback noise for plain strings."""
    try:
        if isinstance(e, BaseException):
            # Use the exception traceback when available.
            logging.error(str(e), exc_info=(type(e), e, e.__traceback__))
        else:
            logging.error(str(e))
    except Exception:
        try:
            logging.error("Unknown logging error")
        except Exception:
            pass

def log_uncaught_exceptions(ex_cls, ex, tb):
    with open(_LOG_PATH, "w", encoding="utf-8") as f:
        traceback.print_exception(ex_cls, ex, tb, file=f)
    print(f"An error occurred. See {_LOG_PATH} for details.")

sys.excepthook = log_uncaught_exceptions

# --- Recursive Extraction Utilities ---
def is_pack_folder(folder):
    """Returns True if manifest.json and pack_icon (png/jpg) exist at root."""
    has_manifest = _os.path.isfile(_os.path.join(folder, 'manifest.json'))
    has_icon = any(
        _os.path.isfile(_os.path.join(folder, f'pack_icon{ext}'))
        for ext in ['.png', '.jpg', '.jpeg']
    )
    return has_manifest and has_icon

def recursive_extract_pack(archive_path, dest_dir=None, max_depth=10):
    """
    Recursively extracts nested mcpack/mcaddon/zip files until it finds a folder with
    manifest.json & pack_icon in the root. It stops extracting deeper at that point.
    Returns a list of all top-level valid pack folders found.
    """
    if max_depth < 1:
        return []
    if dest_dir is None:
        dest_dir = _tempfile.mkdtemp(prefix='mcpack_unpack_')
    packs_found = []

    # Unzip the file to dest_dir
    with _zipfile.ZipFile(archive_path, 'r') as z:
        z.extractall(dest_dir)

    # Case 1: dest_dir itself is a real pack folder
    if is_pack_folder(dest_dir):
        packs_found.append(dest_dir)
        return packs_found

    # Case 2: Multiple .mcpack/.mcaddon/.zip files inside (multi-pack)
    for f in _os.listdir(dest_dir):
        file_path = _os.path.join(dest_dir, f)
        # If it's a nested archive, extract recursively
        if _os.path.isfile(file_path) and f.lower().endswith(('.mcpack', '.mcaddon', '.zip')):
            sub_dest_dir = _tempfile.mkdtemp(prefix='mcpack_unpack_')
            packs_found += recursive_extract_pack(file_path, dest_dir=sub_dest_dir, max_depth=max_depth-1)

        # If it's a folder, check if it's a valid pack
        elif _os.path.isdir(file_path) and is_pack_folder(file_path):
            packs_found.append(file_path)
    return packs_found

def folder_to_mcpack(folder, out_mcpack_path):
    """Zip a folder into a .mcpack file for distribution."""
    with _zipfile.ZipFile(out_mcpack_path, 'w', _zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in _os.walk(folder):
            for file in files:
                file_path = _os.path.join(root, file)
                arcname = _os.path.relpath(file_path, folder)
                zipf.write(file_path, arcname)

class UniversalJsonMerger:
    """
    Universal JSON merger that intelligently merges JSON files based on their structure and context.
    This system detects file types and applies appropriate merge strategies without hardcoding specific packs.
    
    Merge strategies:
    - format_version: Keep highest version
    - scripts.initialize: Concatenate all variable declarations with conflict detection
    - scripts.pre_animation: Concatenate all script lines with duplicate removal
    - scripts.animate: Merge conditions, concatenate animations with compatibility check
    - animations: Smart merge - detect conflicts, merge compatible definitions, warn on incompatibilities
    - materials: Merge dictionaries
    - textures: Merge dictionaries
    - geometry: Keep highest version, merge bones if same geometry ID
    - render_controllers: First-wins per controller ID with conflict detection
    - variables: Merge dictionaries with namespace conflict detection
    - Other arrays: Concatenate with duplicate detection
    - Other dicts: Recursive merge with fallback for non-standard structures
    """
    
    def __init__(self):
        # Keys that should use first-wins strategy (merge by key, keep first definition)
        self.first_wins_keys = {
            'animations', 'animation_controllers', 'render_controllers',
            'materials', 'textures', 'sounds', 'particle_effects'
        }
        
        # Keys that should concatenate arrays
        self.concatenate_keys = {
            'initialize', 'pre_animation', 'animate', 'scripts'
        }
        
        # Keys that should keep highest version (numeric comparison)
        self.version_keys = {'format_version', 'min_engine_version'}
        
        # Keys that are dictionaries but should be merged by key
        self.dict_merge_keys = {
            'variables', 'description'
        }
        
        # Track conflicts for reporting
        self.conflicts = []
        self.warnings = []
    
    def merge_json_list(self, json_list, file_path=None):
        """
        Merge a list of JSON objects into a single merged object.
        Uses context-aware strategies based on the JSON structure.
        """
        if not json_list:
            return {}
        
        # Reset conflict tracking
        self.conflicts = []
        self.warnings = []
        
        # Detect file type from structure
        file_type = self._detect_file_type(json_list[0], file_path)
        
        # Start with first object as base
        merged = json_list[0].copy()
        
        # Merge remaining objects
        for json_obj in json_list[1:]:
            try:
                merged = self._merge_objects(merged, json_obj, file_type, path='')
            except Exception as e:
                # Fallback to simple merge if smart merge fails
                self.warnings.append(f"Smart merge failed for {file_path}, using fallback: {str(e)}")
                merged = self._fallback_merge(merged, json_obj)
        
        # Log conflicts and warnings
        if self.conflicts:
            _logging.warning(f"Merge conflicts detected in {file_path}: {len(self.conflicts)} conflict(s)")
            for conflict in self.conflicts:
                _logging.warning(f"  - {conflict}")
        if self.warnings:
            _logging.warning(f"Merge warnings in {file_path}: {len(self.warnings)} warning(s)")
            for warning in self.warnings:
                _logging.warning(f"  - {warning}")
        
        # Apply universal compatibility patches
        if _UNIVERSAL_PATCHER:
            merged = _UNIVERSAL_PATCHER.patch_merged_file(merged, json_list, file_path)
            patches = _UNIVERSAL_PATCHER.get_patch_report()
            if patches:
                _logging.info(f"Applied {len(patches)} universal compatibility patch(es) to {file_path}")
        
        return merged
    
    def _detect_file_type(self, json_obj, file_path):
        """Detect the type of JSON file based on structure and path."""
        if file_path:
            if 'entity' in file_path and file_path.endswith('.json'):
                if 'client_entity' in file_path or 'minecraft:client_entity' in str(json_obj):
                    return 'client_entity'
                elif 'minecraft:entity' in str(json_obj):
                    return 'entity'
            elif 'item' in file_path:
                return 'item'
            elif 'block' in file_path:
                return 'block'
        
        # Detect from structure
        if 'minecraft:client_entity' in json_obj:
            return 'client_entity'
        elif 'minecraft:entity' in json_obj:
            return 'entity'
        elif 'minecraft:item' in json_obj:
            return 'item'
        elif 'minecraft:block' in json_obj:
            return 'block'
        
        return 'generic'
    
    def _merge_objects(self, base, overlay, file_type, path):
        """
        Recursively merge overlay into base with context-aware strategies.
        """
        for key, value in overlay.items():
            current_path = f"{path}.{key}" if path else key
            
            if key not in base:
                # Key doesn't exist in base, add it
                base[key] = value
            elif isinstance(base[key], dict) and isinstance(value, dict):
                # Both are dicts, merge recursively
                if key in self.first_wins_keys:
                    # First-wins per entry ID with compatibility check
                    for entry_id, entry_data in value.items():
                        if entry_id not in base[key]:
                            base[key][entry_id] = entry_data
                        else:
                            # Entry exists in both, check compatibility
                            if self._are_entries_compatible(base[key][entry_id], entry_data, key):
                                # Compatible, attempt to merge
                                base[key][entry_id] = self._merge_objects(base[key][entry_id], entry_data, file_type, current_path)
                            else:
                                # Incompatible, log conflict and keep first
                                self.conflicts.append(f"Incompatible {key} entry '{entry_id}' at {current_path}")
                elif key in self.dict_merge_keys:
                    # Merge dictionaries with variable conflict detection
                    if key == 'variables':
                        base[key] = self._merge_variables(base[key], value, current_path)
                    else:
                        base[key] = self._merge_objects(base[key], value, file_type, current_path)
                else:
                    # Recursive merge
                    base[key] = self._merge_objects(base[key], value, file_type, current_path)
            elif isinstance(base[key], list) and isinstance(value, list):
                # Both are lists
                if key in self.concatenate_keys or 'scripts' in current_path:
                    # Concatenate arrays with conflict detection
                    if key == 'initialize' or 'initialize' in current_path:
                        # Detect variable redefinitions
                        base[key] = self._concatenate_with_variable_check(base[key], value, current_path)
                    else:
                        # Standard concatenation with duplicate removal
                        base[key] = self._concatenate_unique(base[key], value, current_path)
                else:
                    # Replace with overlay (last wins)
                    base[key] = value
            elif key in self.version_keys:
                # Keep highest version
                base[key] = self._compare_versions(base[key], value)
            else:
                # Primitive values: last wins
                base[key] = value
        
        return base
    
    def _are_entries_compatible(self, entry1, entry2, key_type):
        """
        Check if two entries (animations, controllers, etc.) are compatible for merging.
        Returns True if they can be safely merged, False otherwise.
        """
        # If both are simple values or same structure, they're compatible
        if type(entry1) != type(entry2):
            return False
        
        # For animations/controllers, check if they have similar structure
        if isinstance(entry1, dict) and isinstance(entry2, dict):
            # If they have different keys, they might be incompatible
            keys1 = set(entry1.keys())
            keys2 = set(entry2.keys())
            
            # If one has significantly more keys than the other, they might be different versions
            if abs(len(keys1) - len(keys2)) > 3:
                return False
            
            # Check for critical key differences
            critical_keys = {'loops', 'blend_expression', 'anim_time_update', 'transition_duration'}
            for critical_key in critical_keys:
                if critical_key in keys1 and critical_key in keys2:
                    if entry1[critical_key] != entry2[critical_key]:
                        return False
        
        return True
    
    def _merge_variables(self, base_vars, overlay_vars, path):
        """
        Merge variable dictionaries with conflict detection.
        Warns if variables are redefined with different values.
        """
        for var_name, var_value in overlay_vars.items():
            if var_name not in base_vars:
                base_vars[var_name] = var_value
            elif base_vars[var_name] != var_value:
                # Variable redefined with different value
                self.warnings.append(f"Variable '{var_name}' redefined with different value at {path}")
                # Keep the overlay value (last wins)
                base_vars[var_name] = var_value
        
        return base_vars
    
    def _concatenate_with_variable_check(self, base_list, overlay_list, path):
        """
        Concatenate script arrays with variable redefinition detection.
        """
        # Extract variable declarations from both lists
        base_vars = self._extract_variables(base_list)
        overlay_vars = self._extract_variables(overlay_list)
        
        # Check for conflicts
        for var_name in overlay_vars:
            if var_name in base_vars and base_vars[var_name] != overlay_vars[var_name]:
                self.warnings.append(f"Variable '{var_name}' redefined in scripts at {path}")
        
        # Concatenate with duplicate removal
        return self._concatenate_unique(base_list, overlay_list, path)
    
    def _extract_variables(self, script_list):
        """
        Extract variable declarations from a script array.
        Returns dict of variable_name -> initial_value
        """
        variables = {}
        for item in script_list:
            if isinstance(item, str):
                # Match patterns like "variable.name = value" or "v.name = value"
                import re
                match = re.search(r'(?:variable|v)\.(\w+)\s*=\s*(.+)', item)
                if match:
                    var_name = match.group(1)
                    var_value = match.group(2).strip()
                    variables[var_name] = var_value
        return variables
    
    def _concatenate_unique(self, base_list, overlay_list, path):
        """
        Concatenate two lists while avoiding duplicates.
        """
        existing = set(str(item) for item in base_list)
        result = list(base_list)
        
        for item in overlay_list:
            item_str = str(item)
            if item_str not in existing:
                result.append(item)
                existing.add(item_str)
        
        return result
    
    def _fallback_merge(self, base, overlay):
        """
        Fallback merge for non-standard JSON structures.
        Uses simple last-wins strategy for all values.
        """
        try:
            for key, value in overlay.items():
                if key not in base:
                    base[key] = value
                elif isinstance(base[key], dict) and isinstance(value, dict):
                    base[key] = self._fallback_merge(base[key], value)
                elif isinstance(base[key], list) and isinstance(value, list):
                    # Simple concatenation for lists
                    base[key] = base[key] + value
                else:
                    base[key] = value
        except Exception as e:
            self.warnings.append(f"Fallback merge error: {str(e)}")
        
        return base
    
    def _compare_versions(self, v1, v2):
        """Compare two version values and return the highest."""
        try:
            # Handle list versions like [1, 26, 0]
            if isinstance(v1, list) and isinstance(v2, list):
                for a, b in zip(v1, v2):
                    if a > b:
                        return v1
                    elif b > a:
                        return v2
                return v1  # Equal, keep first
            # Handle string versions like "1.26.0"
            elif isinstance(v1, str) and isinstance(v2, str):
                v1_parts = [int(x) for x in v1.split('.')]
                v2_parts = [int(x) for x in v2.split('.')]
                for a, b in zip(v1_parts, v2_parts):
                    if a > b:
                        return v1
                    elif b > a:
                        return v2
                return v1
        except:
            pass
        # If comparison fails, keep overlay (last wins)
        return v2


class IdentifierManager:
    """
    Manages identifier conflicts by:
    1. Scanning all identifiers in packs
    2. Detecting conflicts
    3. Generating unique namespaces
    4. Prefixing identifiers
    5. Tracking and updating references
    """
    
    def __init__(self):
        self.all_identifiers = defaultdict(set)  # type -> set of identifiers
        self.pack_identifiers = {}  # pack_path -> {type -> set of identifiers}
        self.identifier_mapping = {}  # (pack_path, old_id) -> new_id
        self.pack_namespaces = {}  # pack_path -> namespace_prefix
        self.conflict_map = defaultdict(set)  # identifier -> {pack_paths}
        self.reference_files = defaultdict(set)  # identifier -> set of file_paths
        # User resolution: identifier -> pack_path to keep (None = keep all / prefix)
        self.user_resolution = {}
        
    def scan_pack_identifiers(self, pack_zip, pack_path):
        """
        Scan a pack for all identifiers (entities, items, blocks, loot tables, recipes).
        Returns dict of identifier types and their values.
        """
        identifiers = {
            'entities': set(),
            'items': set(),
            'blocks': set(),
            'loot_tables': set(),
            'recipes': set(),
            'animation_controllers': set(),
            'render_controllers': set(),
            'textures': set()
        }
        
        try:
            for item_name in pack_zip.namelist():
                if item_name.startswith('subpacks/'):
                    continue
                    
                # Scan entity files
                if item_name.startswith('entities/') and item_name.endswith('.json'):
                    identifiers['entities'].update(self._extract_entity_identifiers(pack_zip, item_name))
                    
                # Scan item files
                if item_name.startswith('items/') and item_name.endswith('.json'):
                    identifiers['items'].update(self._extract_item_identifiers(pack_zip, item_name))
                    
                # Scan block files
                if item_name.startswith('blocks/') and item_name.endswith('.json'):
                    identifiers['blocks'].update(self._extract_block_identifiers(pack_zip, item_name))
                    
                # Scan loot tables
                if item_name.startswith('loot_tables/') and item_name.endswith('.json'):
                    loot_id = self._extract_loot_table_id(item_name)
                    if loot_id:
                        identifiers['loot_tables'].add(loot_id)
                        
                # Scan recipes
                if item_name.startswith('recipes/') and item_name.endswith('.json'):
                    identifiers['recipes'].update(self._extract_recipe_identifiers(pack_zip, item_name))
                    
                # Scan animation controllers
                if 'animation_controllers' in item_name and item_name.endswith('.json'):
                    identifiers['animation_controllers'].update(self._extract_animation_controller_identifiers(pack_zip, item_name))
                    
                # Scan render controllers
                if 'render_controllers' in item_name and item_name.endswith('.json'):
                    identifiers['render_controllers'].update(self._extract_render_controller_identifiers(pack_zip, item_name))
                    
        except Exception as e:
            _logging.warning(f"Error scanning identifiers in {pack_path}: {e}")
            
        return identifiers
    
    def _extract_entity_identifiers(self, pack_zip, item_name):
        """Extract entity identifiers from entity JSON file."""
        identifiers = set()
        try:
            with pack_zip.open(item_name) as f:
                content = f.read().decode('utf-8', errors='ignore')
                # Remove comments
                content = _re.sub(r'//.*?$|/\*.*?\*/', '', content, flags=_re.MULTILINE | _re.DOTALL)
                try:
                    data = _json.loads(content)
                    # Check for minecraft:entity or minecraft:client_entity
                    for key in ['minecraft:entity', 'minecraft:client_entity']:
                        if key in data:
                            desc = data[key].get('description', {})
                            entity_id = desc.get('identifier')
                            if entity_id and entity_id != 'minecraft:player':
                                identifiers.add(entity_id)
                except:
                    pass
        except:
            pass
        return identifiers
    
    def _extract_item_identifiers(self, pack_zip, item_name):
        """Extract item identifiers from item JSON file."""
        identifiers = set()
        try:
            with pack_zip.open(item_name) as f:
                content = f.read().decode('utf-8', errors='ignore')
                content = _re.sub(r'//.*?$|/\*.*?\*/', '', content, flags=_re.MULTILINE | _re.DOTALL)
                try:
                    data = _json.loads(content)
                    if 'minecraft:item' in data:
                        desc = data['minecraft:item'].get('description', {})
                        item_id = desc.get('identifier')
                        if item_id:
                            identifiers.add(item_id)
                except:
                    pass
        except:
            pass
        return identifiers
    
    def _extract_block_identifiers(self, pack_zip, item_name):
        """Extract block identifiers from block JSON file."""
        identifiers = set()
        try:
            with pack_zip.open(item_name) as f:
                content = f.read().decode('utf-8', errors='ignore')
                content = _re.sub(r'//.*?$|/\*.*?\*/', '', content, flags=_re.MULTILINE | _re.DOTALL)
                try:
                    data = _json.loads(content)
                    if 'minecraft:block' in data:
                        desc = data['minecraft:block'].get('description', {})
                        block_id = desc.get('identifier')
                        if block_id:
                            identifiers.add(block_id)
                except:
                    pass
        except:
            pass
        return identifiers
    
    def _extract_loot_table_id(self, item_name):
        """Extract loot table identifier from file path."""
        # Format: loot_tables/entities/zombie.json -> minecraft:entities/zombie
        if item_name.startswith('loot_tables/'):
            path_part = item_name[12:]  # Remove 'loot_tables/'
            if path_part.endswith('.json'):
                path_part = path_part[:-5]  # Remove '.json'
                # Convert path to identifier format
                parts = path_part.split('/')
                if len(parts) >= 2:
                    return f"{parts[0]}:{'/'.join(parts[1:])}"
                elif len(parts) == 1:
                    return f"loot_tables:{parts[0]}"
        return None
    
    def _extract_recipe_identifiers(self, pack_zip, item_name):
        """Extract recipe identifiers from recipe JSON file."""
        identifiers = set()
        try:
            with pack_zip.open(item_name) as f:
                content = f.read().decode('utf-8', errors='ignore')
                content = _re.sub(r'//.*?$|/\*.*?\*/', '', content, flags=_re.MULTILINE | _re.DOTALL)
                try:
                    data = _json.loads(content)
                    # Recipes can have identifier in description or as key
                    if 'minecraft:recipe_furnace' in data or 'minecraft:recipe_shaped' in data or 'minecraft:recipe_shapeless' in data:
                        for key in data.keys():
                            if 'recipe' in key.lower():
                                recipe_data = data[key]
                                if isinstance(recipe_data, dict):
                                    desc = recipe_data.get('description', {})
                                    recipe_id = desc.get('identifier')
                                    if recipe_id:
                                        identifiers.add(recipe_id)
                except:
                    pass
        except:
            pass
        return identifiers
    
    def _extract_animation_controller_identifiers(self, pack_zip, item_name):
        """Extract animation controller identifiers."""
        identifiers = set()
        try:
            with pack_zip.open(item_name) as f:
                content = f.read().decode('utf-8', errors='ignore')
                content = _re.sub(r'//.*?$|/\*.*?\*/', '', content, flags=_re.MULTILINE | _re.DOTALL)
                try:
                    data = _json.loads(content)
                    # Animation controllers are keyed by identifier
                    for key in data.keys():
                        if ':' in key:  # Has namespace:name format
                            identifiers.add(key)
                except:
                    pass
        except:
            pass
        return identifiers
    
    def _extract_render_controller_identifiers(self, pack_zip, item_name):
        """Extract render controller identifiers."""
        identifiers = set()
        try:
            with pack_zip.open(item_name) as f:
                content = f.read().decode('utf-8', errors='ignore')
                content = _re.sub(r'//.*?$|/\*.*?\*/', '', content, flags=_re.MULTILINE | _re.DOTALL)
                try:
                    data = _json.loads(content)
                    # Render controllers are keyed by identifier
                    for key in data.keys():
                        if ':' in key:
                            identifiers.add(key)
                except:
                    pass
        except:
            pass
        return identifiers
    
    def detect_conflicts(self, all_pack_identifiers):
        """
        Detect identifier conflicts across all packs.
        all_pack_identifiers: dict of pack_path -> identifiers dict
        """
        # Aggregate all identifiers by type
        type_identifiers = defaultdict(set)
        self.pack_identifiers = all_pack_identifiers
        
        for pack_path, identifiers in all_pack_identifiers.items():
            for id_type, id_set in identifiers.items():
                type_identifiers[id_type].update(id_set)
                # Track which packs use each identifier
                for identifier in id_set:
                    # Skip the entire minecraft: namespace — those are vanilla entity/item/block
                    # modifications that should always be deep-merged, never renamed or flagged.
                    # Also skip loot_tables: — vanilla loot table references included by many packs.
                    ns = identifier.split(':')[0] if ':' in identifier else ''
                    if ns in ('minecraft', 'loot_tables'):
                        continue
                    self.conflict_map[identifier].add(pack_path)
        
        # Generate namespace prefixes for each pack
        for idx, pack_path in enumerate(all_pack_identifiers.keys()):
            # Create unique namespace prefix (pack1_merge, pack2_merge, etc.)
            pack_name = _os.path.basename(pack_path).replace('.mcpack', '').replace('.mcaddon', '')
            # Clean up pack name for namespace (only alphanumeric and underscore)
            clean_name = _re.sub(r'[^a-zA-Z0-9_]', '_', pack_name)[:20]
            self.pack_namespaces[pack_path] = f"{clean_name}_merge"
    
    @staticmethod
    def _pack_base_name(pack_path):
        """Strip AutoBE's internal suffixes so BP/RP halves of the same addon compare equal."""
        name = _os.path.basename(pack_path)
        name = _re.sub(r'\.(mcpack|mcaddon)$', '', name, flags=_re.IGNORECASE)
        # Strip _modified (subpack-extracted temp copy) then _N split suffix, in that order
        name = _re.sub(r'_modified$', '', name, flags=_re.IGNORECASE)
        name = _re.sub(r'_\d+$', '', name)
        # Strip common BP/RP halve suffixes so paired addon halves resolve to the same base name
        name = _re.sub(
            r'[_\-\s]*(bp|rp|behaviors?|resources?|behavior[_\-]?pack|resource[_\-]?pack)$',
            '', name, flags=_re.IGNORECASE)
        return name.lower()

    def get_conflict_list(self):
        """Return list of (identifier, list of pack_paths) for all conflicted identifiers.
        Excludes false conflicts where every involved pack is a BP/RP half of the same addon
        (identified by sharing the same base name after stripping AutoBE's _N split suffix)."""
        result = []
        for identifier, packs in self.conflict_map.items():
            if len(packs) <= 1:
                continue
            base_names = {self._pack_base_name(p) for p in packs}
            if len(base_names) == 1:
                # All packs are halves of the same addon — not a real conflict
                continue
            result.append((identifier, list(packs)))
        return result

    def set_user_resolution(self, identifier, pack_path_or_none):
        """Set user choice for a conflicted identifier: pack_path to keep, or None to keep all (prefix)."""
        self.user_resolution[identifier] = pack_path_or_none

    def should_include_definition(self, pack_path, identifier):
        """Return True if this pack's definition of the identifier should be included in the merge.
        If user chose to keep one pack only, other packs' definitions are excluded."""
        if identifier not in self.user_resolution:
            return True
        keep = self.user_resolution[identifier]
        if keep is None:
            return True
        return pack_path == keep

    def generate_identifier_mappings(self):
        """
        Generate identifier mappings.
        'Keep all' (default/None) = no renaming; the entity/item/block merge system
        combines definitions naturally so identifiers stay intact and all references work.
        Only 'Keep one pack' (explicit pack_path) generates a mapping entry (to filter others).
        """
        conflicted_identifiers = {id: packs for id, packs in self.conflict_map.items() if len(packs) > 1}

        for identifier, pack_paths in conflicted_identifiers.items():
            keep_pack = self.user_resolution.get(identifier)
            if keep_pack is not None:
                # User explicitly chose one pack — all packs map to the original id
                # (filtering is handled by should_include_definition; the winner keeps its id)
                for pack_path in pack_paths:
                    self.identifier_mapping[(pack_path, identifier)] = identifier
            # 'Keep all' (keep_pack is None): no rename mapping created.
            # All packs' definitions pass through; the merge system deep-merges them
            # under the original identifier so every reference in every file stays valid.

        _logging.info(f"Generated {len(self.identifier_mapping)} identifier mappings (renaming disabled for merge mode)")
    
    def get_new_identifier(self, pack_path, old_identifier):
        """Get the new identifier for a given pack and old identifier."""
        return self.identifier_mapping.get((pack_path, old_identifier), old_identifier)
    
    def should_rename_identifier(self, identifier):
        """Check if an identifier needs to be renamed (has conflicts)."""
        return len(self.conflict_map.get(identifier, [])) > 1
    
    def update_json_identifiers(self, json_data, pack_path):
        """
        Recursively update all identifier references in JSON data.
        Returns updated JSON data structure.
        """
        if isinstance(json_data, dict):
            updated = {}
            for key, value in json_data.items():
                # Update identifier fields
                if key == 'identifier' and isinstance(value, str):
                    updated[key] = self.get_new_identifier(pack_path, value)
                elif key in ['entity', 'item', 'block', 'loot_table', 'recipe'] and isinstance(value, str):
                    # Update references to entities/items/blocks
                    updated[key] = self.get_new_identifier(pack_path, value)
                else:
                    # Recursively update nested structures
                    updated[key] = self.update_json_identifiers(value, pack_path)
            return updated
        elif isinstance(json_data, list):
            return [self.update_json_identifiers(item, pack_path) for item in json_data]
        elif isinstance(json_data, str):
            # Check if string is an identifier reference (contains :)
            if ':' in json_data and not json_data.startswith('http'):
                # Try to update if it matches a known identifier
                new_id = self.get_new_identifier(pack_path, json_data)
                return new_id
        return json_data
    
    def update_text_identifiers(self, text, pack_path):
        """
        Update identifier references in text content (scripts, lang files, etc.).
        Uses regex to find and replace identifier patterns.
        """
        # Pattern to match identifiers (namespace:name format)
        identifier_pattern = r'\b([a-zA-Z0-9_]+:[a-zA-Z0-9_\./]+)\b'
        
        def replace_identifier(match):
            old_id = match.group(1)
            new_id = self.get_new_identifier(pack_path, old_id)
            return new_id
        
        updated_text = _re.sub(identifier_pattern, replace_identifier, text)
        return updated_text

def find_valid_packs(entry, max_depth=10):
    """
    Recursively find all pack folders (manifest.json at root) inside entry.
    Returns a list of absolute paths to valid pack folders.
    """
    found = []
    if max_depth < 1:
        return []
    if _os.path.isdir(entry):
        if _os.path.isfile(_os.path.join(entry, 'manifest.json')):
            found.append(entry)
            return found
        for child in _os.listdir(entry):
            child_path = _os.path.join(entry, child)
            found += find_valid_packs(child_path, max_depth-1)
        return found
    ext = _os.path.splitext(entry)[1].lower()
    if ext in ('.mcpack', '.mcaddon', '.zip'):
        tempdir = _tempfile.mkdtemp(prefix='mcpacker_temp_')
        try:
            with _zipfile.ZipFile(entry, 'r') as z:
                z.extractall(tempdir)
            for item in _os.listdir(tempdir):
                child_path = _os.path.join(tempdir, item)
                found += find_valid_packs(child_path, max_depth-1)
            if _os.path.isfile(_os.path.join(tempdir, 'manifest.json')):
                found.append(tempdir)
        except Exception as e:
            print(f"Failed to unzip {entry}: {e}")
        # Don't delete tempdir here! (wait until after zipping result)
    return found

def zip_pack_folder(folder, output_mcpack_path):
    with _zipfile.ZipFile(output_mcpack_path, 'w', _zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in _os.walk(folder):
            rel = _os.path.relpath(root, folder)
            for file in files:
                abs_path = _os.path.join(root, file)
                arcname = _os.path.join(rel, file) if rel != '.' else file
                zf.write(abs_path, arcname)

def safe_decode(byte_data):
    try:
        return byte_data.decode('utf-8')
    except UnicodeDecodeError:
        return byte_data.decode('latin-1')

class _T1:
    def __init__(self, _p1):
        self._p1 = _p1
        self._agreed = False  # True only after user clicks Agree
        self._terms_scrolled_to_bottom = False
        self._drag_offset_x = 0
        self._drag_offset_y = 0
        self._w1 = _tk.Toplevel(_p1)
        _apply_window_icon_global(self._w1)
        self._w1.title(_("tos.window_title"))
        self._w1.geometry("840x620")
        self._w1.configure(bg='#000000')
        self._w1.overrideredirect(True)
        # Single taskbar fix attempt to show icon in taskbar
        self._w1.after(100, lambda: _force_taskbar_button(self._w1))
        self._w1.grid_columnconfigure(0, weight=1)
        self._w1.grid_rowconfigure(0, weight=0)
        self._w1.grid_rowconfigure(1, weight=1)
        self._w1.grid_rowconfigure(2, weight=0)
        # If user closes via X instead of Agree, exit the app (must agree to use)
        self._w1.protocol("WM_DELETE_WINDOW", self._on_close_x)

        # Custom dark title bar (guaranteed black style)
        titlebar = _tk.Frame(self._w1, bg="#000000", height=36, highlightthickness=1, highlightbackground="#1f1f1f")
        titlebar.grid(row=0, column=0, sticky="ew")
        titlebar.grid_columnconfigure(1, weight=1)
        titlebar.grid_propagate(False)
        self._tos_title_icon_img = _get_titlebar_icon_image(14)
        if self._tos_title_icon_img is not None:
            title_icon = _tk.Label(titlebar, image=self._tos_title_icon_img, bg="#000000")
        else:
            title_icon = _tk.Label(titlebar, text="◈", bg="#000000", fg="#9333ea", font=("Segoe UI", 10, "bold"))
        title_icon.grid(row=0, column=0, padx=(10, 6), sticky="w")
        title_lbl = _tk.Label(titlebar, text=_("tos.window_title"), bg="#000000", fg="#E5E7EB", font=("Segoe UI", 10))
        title_lbl.grid(row=0, column=1, padx=(0, 6), sticky="w")
        close_btn = _tk.Button(titlebar, text="✕", command=self._on_close_x, bg="#000000", fg="#E5E7EB",
                               font=("Segoe UI", 10, "bold"), relief="flat", bd=0, padx=12, pady=3,
                               activebackground="#c42b1c", activeforeground="#FFFFFF", cursor="hand2")
        close_btn.grid(row=0, column=2, sticky="e")
        for w in (titlebar, title_icon, title_lbl):
            w.bind("<ButtonPress-1>", self._drag_start, add="+")
            w.bind("<B1-Motion>", self._drag_move, add="+")

        # Main container
        container = _tk.Frame(self._w1, bg='#000000')
        container.grid(row=1, column=0, sticky="nsew", padx=16, pady=(12, 8))
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(1, weight=1)

        self._tos_hint_label = _tk.Label(
            container,
            text="Read and scroll to the bottom to enable Agree.",
            bg="#000000",
            fg="#9CA3AF",
            font=("Segoe UI", 10),
        )
        self._tos_hint_label.grid(row=0, column=0, sticky="w", pady=(0, 8))

        # Terms body
        self._t1 = _tk.Text(
            container,
            wrap=_tk.WORD,
            bg='#0A0A0A',
            fg='#FFFFFF',
            font=("Segoe UI", 11),
            insertbackground='#a855f7',
            relief='flat',
            bd=0,
            padx=12,
            pady=10,
        )
        self._t1.grid(row=1, column=0, sticky="nsew")
        self._t1.bind("<MouseWheel>", self._on_terms_mousewheel, add="+")
        self._t1.bind("<Button-4>", self._on_terms_mousewheel, add="+")
        self._t1.bind("<Button-5>", self._on_terms_mousewheel, add="+")
        self._t1.bind("<Configure>", lambda _e: self._check_terms_scrolled_to_bottom(), add="+")

        _terms_text = _get_tos_text() or ("SOFTWARE LICENSE AGREEMENT\n\n" + _("tos.window_title"))
        self._t1.insert(_tk.END, _terms_text)
        self._t1.config(state=_tk.DISABLED)

        # Footer actions
        button_frame = _tk.Frame(self._w1, bg='#000000')
        button_frame.grid(row=2, column=0, sticky="ew", padx=16, pady=(4, 14))
        button_frame.grid_columnconfigure(0, weight=1)

        action_frame = _tk.Frame(button_frame, bg="#000000")
        action_frame.grid(row=0, column=1, sticky="e")

        self._decline_btn = _tk.Button(
            action_frame,
            text="✕ Decline",
            command=self._on_close_x,
            bg="#1f1f1f",
            fg="#FFFFFF",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            cursor="hand2",
            activebackground="#2d2d2d",
            padx=16,
            pady=8,
        )
        self._decline_btn.pack(side=_tk.LEFT, padx=(0, 10))

        self._b1 = _tk.Button(
            action_frame,
            text="✓ " + _("activation.i_agree") + " (scroll to bottom)",
            command=self._accept,
            bg="#3a3a3a",
            fg="#8f8f8f",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            cursor="arrow",
            activebackground="#3a3a3a",
            activeforeground="#8f8f8f",
            disabledforeground="#8f8f8f",
            state=_tk.DISABLED,
            padx=16,
            pady=8,
        )
        self._b1.pack(side=_tk.LEFT)
        self._w1.after(50, self._check_terms_scrolled_to_bottom)

    def _drag_start(self, event):
        self._drag_offset_x = event.x_root - self._w1.winfo_x()
        self._drag_offset_y = event.y_root - self._w1.winfo_y()

    def _drag_move(self, event):
        x = event.x_root - self._drag_offset_x
        y = event.y_root - self._drag_offset_y
        self._w1.geometry(f"+{x}+{y}")

    def _on_terms_mousewheel(self, event):
        try:
            if getattr(event, "num", None) == 4:
                self._t1.yview_scroll(-3, "units")
            elif getattr(event, "num", None) == 5:
                self._t1.yview_scroll(3, "units")
            else:
                delta = int(getattr(event, "delta", 0))
                if delta != 0:
                    # Windows/macOS wheel delta handling.
                    self._t1.yview_scroll(int(-delta / 120) * 3, "units")
            self._check_terms_scrolled_to_bottom()
        except Exception:
            pass
        return "break"

    def _check_terms_scrolled_to_bottom(self):
        if self._terms_scrolled_to_bottom:
            return
        try:
            _first, last = self._t1.yview()
            # Lower threshold to 0.95 to account for text widget padding and rendering differences
            if float(last) >= 0.95:
                self._terms_scrolled_to_bottom = True
                self._tos_hint_label.config(text="You reached the end. You can now agree.", fg="#C4B5FD")
                self._b1.config(
                    state=_tk.NORMAL,
                    text="✓ " + _("activation.i_agree"),
                    bg="#9333ea",
                    fg="#FFFFFF",
                    activebackground="#a855f7",
                    activeforeground="#FFFFFF",
                    cursor="hand2",
                )
        except Exception:
            pass

    def _accept(self):
        if not self._terms_scrolled_to_bottom:
            _messagebox.showinfo(
                _("tos.window_title"),
                "Please scroll to the bottom of the terms before accepting.",
            )
            return
        self._agreed = True
        # Smooth transition: withdraw TOS window first
        self._w1.withdraw()
        self._w1.update_idletasks()
        # Destroy TOS window after transition
        self._w1.after(50, self._w1.destroy)
        # Show main window smoothly
        self._p1.deiconify()
        self._p1.lift()
        self._p1.focus_force()
        self._p1.update_idletasks()
        # Apply taskbar fixes with minimal delay to reduce flickering
        self._p1.after(150, lambda: _force_taskbar_button(self._p1))
        self._p1.after(300, lambda: _apply_window_icon(self._p1))

    def _on_close_x(self):
        """User closed terms window without agreeing; close the app. Do nothing if they clicked Agree (destroy can trigger this)."""
        if self._agreed:
            return
        try:
            self._w1.destroy()
        except Exception:
            pass
        try:
            self._p1.destroy()
        except Exception:
            pass
        _os._exit(0)

class _ActivationWindow:
    def __init__(self, _p1):
        self._p1 = _p1
        self._w1 = _tk.Toplevel(_p1)
        _apply_window_icon_global(self._w1)
        self._w1.title("Enter Activation Key")
        self._w1.geometry("400x200")
        self._w1.configure(bg='#0A0A0A')

        self._label = _tk.Label(self._w1, text=_("activation.enter_key"), bg='#0A0A0A', fg='#E1E1E1', font=("Helvetica", 12))
        self._label.pack(pady=10)

        self._entry_key = _tk.Entry(self._w1, width=40, bg='#1A1A1A', fg='#A50CAC', font=("Helvetica", 12))
        self._entry_key.pack(pady=10)

        self._btn_submit = _tk.Button(self._w1, text=_("activation.submit"), command=self._submit_key, bg='#A50CAC', fg='#FFFFFF', font=("Helvetica", 12, "bold"))
        self._btn_submit.pack(pady=10)

    def _fetch_github_file(self, file_path):
        """Fetch a file from GitHub using the API with token. Returns None if network/DNS fails (offline)."""
        _headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        api_url = f"https://api.github.com/repos/FrostyHostMC/AutoBE/contents/{file_path}"
        try:
            response = _requests.get(api_url, headers=_headers, timeout=10)
            response.raise_for_status()
            file_data = response.json()
            content = base64.b64decode(file_data['content']).decode('utf-8')
            return content
        except (_requests.exceptions.ConnectionError, _requests.exceptions.Timeout, _requests.exceptions.HTTPError, OSError) as e:
            _logging.debug("GitHub fetch failed (network/HTTP error): %s", e)
            return None
        except Exception:
            raise

    def _submit_key(self):
        _key = self._entry_key.get().strip()

        if not _key:
            _messagebox.showerror(_("msg.error"), _("activation.enter_key_error"))
            return

        try:
            # Fetch the current list of valid keys using the helper function
            keys_text = self._fetch_github_file("keys.csv")
            if keys_text is None:
                _messagebox.showerror(_("msg.error"), _("msg.connection_error") if _("msg.connection_error") != "msg.connection_error" else "Cannot reach server. Check your internet connection and try again.")
                return
            response_text = keys_text

            # Parse CSV - try multiple methods to handle various formats
            valid_keys = []
            
            # Method 1: Try CSV reader (handles quoted values)
            try:
                csv_reader = csv.reader(io.StringIO(response_text), quoting=csv.QUOTE_MINIMAL)
                for row in csv_reader:
                    for key in row:
                        key = key.strip()
                        # Normalize key: remove spaces (consistent with input normalization)
                        key_normalized = key.replace(' ', '')
                        if key_normalized:
                            valid_keys.append(key_normalized)
            except Exception as e:
                log_error(f"CSV reader failed: {e}")
            
            # Method 2: Also try simple line-by-line parsing (in case CSV format is different)
            if not valid_keys:
                for line in response_text.splitlines():
                    line = line.strip()
                    if line:
                        # Remove CSV quotes if present
                        if line.startswith('"') and line.endswith('"'):
                            line = line[1:-1]
                        # Handle escaped quotes
                        line = line.replace('""', '"')
                        # Normalize: remove spaces
                        key_normalized = line.replace(' ', '')
                        if key_normalized:
                            valid_keys.append(key_normalized)
            
            # Remove any spaces from input key (in case user accidentally added spaces)
            normalized_input = _key.strip().replace(' ', '')
            
            # Debug logging
            _logging.debug(f"Looking for key: {normalized_input}")
            _logging.debug(f"Found {len(valid_keys)} keys in CSV")
            if len(valid_keys) <= 10:  # Only log if reasonable number
                _logging.debug(f"Valid keys: {valid_keys}")

            # Try exact match first
            if normalized_input not in valid_keys:
                # Try case-insensitive match (in case there's a case mismatch)
                normalized_lower = normalized_input.lower()
                matched_key = None
                for key in valid_keys:
                    if key.lower() == normalized_lower:
                        matched_key = key
                        break
                
                if matched_key:
                    # Use the matched key (preserve original case from CSV)
                    normalized_input = matched_key
                else:
                    _messagebox.showerror(_("msg.error"), _("activation.invalid_key"))
                    return

            # Remove the key from keys.csv (use normalized key)
            valid_keys.remove(normalized_input)
            self._update_keys_csv(valid_keys)

            _hwid = self._generate_hwid()
            self._append_hwid(_hwid)

            # Notify the user and close the activation window
            _messagebox.showinfo(_("msg.success"), _("activation.success_msg"))
            self._send_discord_notification(_key)
            self._w1.destroy()
            self._p1.destroy()

        except Exception as e:
            log_error(e)
            _messagebox.showerror(_("msg.error"), _f("activation.validate_failed", error=str(e)))

    def _update_keys_csv(self, valid_keys):
        """Update the keys.csv file by removing the used key"""
        _keys_file_url = "https://api.github.com/repos/FrostyHostMC/AutoBE/contents/keys.csv"
        _headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Content-Type": "application/json"
        }
        # Recreate the keys.csv content using proper CSV formatting
        output = io.StringIO()
        csv_writer = csv.writer(output)
        # Write each key as a separate row (properly handles special characters)
        for key in valid_keys:
            csv_writer.writerow([key])
        new_content = output.getvalue().encode('utf-8')
        
        # Base64 encode the content
        encoded_content = base64.b64encode(new_content).decode('utf-8')
        
        try:
            # Get the SHA of the current file
            response = _requests.get(_keys_file_url, headers=_headers)
            response.raise_for_status()
            sha = response.json()['sha']

            # Update the file on GitHub with the new content
            update_data = {
                "message": "Remove used activation key",
                "content": encoded_content,
                "sha": sha
            }
            response = _requests.put(_keys_file_url, json=update_data, headers=_headers)
            response.raise_for_status()
        except Exception as e:
            log_error(e)
            raise Exception(f"Failed to update keys.csv: {str(e)}")

    def _append_hwid(self, _hwid):
        _hwid_file_url = "https://api.github.com/repos/FrostyHostMC/AutoBE/contents/hwid_address.txt"
        _headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Content-Type": "application/json"
        }
        try:
            response = _requests.get(_hwid_file_url, headers=_headers)
            response.raise_for_status()
            
            file_data = response.json()
            current_content = base64.b64decode(file_data['content']).decode('utf-8').rstrip()
            sha = file_data['sha']

            updated_content = f"{current_content}\n{_hwid}\n"
            encoded_content = base64.b64encode(updated_content.encode('utf-8')).decode('utf-8')
            
            update_data = {
                "message": "Add new HWID",
                "content": encoded_content,
                "sha": sha
            }
            put_response = _requests.put(_hwid_file_url, json=update_data, headers=_headers)
            put_response.raise_for_status()
            
            return put_response.json()

        except _requests.exceptions.RequestException as req_err:
            log_error(req_err)
            raise Exception(f"HTTP request failed: {str(req_err)}")
        except Exception as e:
            log_error(e)
            raise Exception(f"Failed to update hwid_address.txt: {str(e)}")

    def _send_discord_notification(self, _key):
        _hwid = self._generate_hwid()
        _webhook_url = os.environ.get("AUTOBE_KEY_WEBHOOK", "")
        if not _webhook_url:
            return
        _data = {
            "content": f"Activation key used: {_key}\nHWID: {_hwid}"
        }
        _requests.post(_webhook_url, json=_data)

    def _generate_hwid(self):
        """Generate a hardware-based unique identifier."""
        if platform.system() == "Windows":
            # Try PowerShell Get-CimInstance (modern replacement for WMIC)
            try:
                ps_command = "Get-CimInstance -ClassName Win32_ComputerSystemProduct | Select-Object -ExpandProperty UUID"
                output = subprocess.check_output(
                    ["powershell", "-Command", ps_command],
                    stderr=subprocess.STDOUT,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
                ).strip()
                if output:
                    return output
            except Exception:
                pass
            # Try WMIC (legacy, may not work on newer Windows)
            try:
                output = subprocess.check_output(
                    ["wmic", "csproduct", "get", "uuid"],
                    stderr=subprocess.STDOUT,
                    text=True
                ).splitlines()
                uuid_value = next(
                    (line.strip() for line in output if line.strip() and line.strip().lower() != "uuid"),
                    None
                )
                if uuid_value:
                    return uuid_value
            except Exception:
                pass
            # Fallback if both methods fail
            return hashlib.md5(platform.node().encode()).hexdigest()
        elif platform.system() == "Linux":
            try:
                with open("/etc/machine-id", "r") as f:
                    return f.read().strip()
            except Exception as e:
                # Fallback if file read fails
                return hashlib.md5(platform.node().encode()).hexdigest()
        elif platform.system() == "Darwin":
            try:
                command = "system_profiler SPHardwareDataType | grep 'Hardware UUID'"
                uuid = subprocess.check_output(command, shell=True).decode().split(": ")[1].strip()
                return uuid
            except Exception as e:
                # Fallback if shell command fails
                return hashlib.md5(platform.node().encode()).hexdigest()
        else:
            return hashlib.md5(platform.node().encode()).hexdigest()

class AutoBEApp:
    def __init__(self, _root):
        self._root = _root
        self._pending_update_result = _consume_post_update_result_arg()
        self._is_maximized = False
        self._restore_geometry = None
        self._drag_offset_x = 0
        self._drag_offset_y = 0
        # Register AppUserModelID before any window draws so the taskbar
        # button gets its own slot with the correct icon from the start.
        _set_app_user_model_id()
        if platform.system() == "Windows" and not getattr(sys, "frozen", False):
            for _ms in (50, 150, 350, 600, 1000):
                self._root.after(_ms, _hide_console_window)
        self._root.title("AutoBE - CodeNex")
        self._apply_window_icon(self._root)
        self._root.geometry("900x800")
        self._root.minsize(900, 800)
        # Modern dark theme background - pure black for activation window
        self._root.configure(bg='#000000')
        # Use custom title bar so we never show white native caption.
        self._root.overrideredirect(True)
        # Hide main window initially - will be shown after terms are accepted
        self._root.withdraw()
        # Don't apply taskbar fixes - they cause flickering with withdraw/deiconify
        # Taskbar button will appear naturally when window is shown

        # Allow the main window to be resized
        self._root.columnconfigure(0, weight=1)
        self._root.rowconfigure(0, weight=0)  # custom title bar
        self._root.rowconfigure(1, weight=1)  # app content
        self._init_custom_title_bar()

        # Create activation overlay frame (shown first, covers everything)
        self._activation_overlay = _tk.Frame(self._root, bg='#000000')
        self._activation_overlay.grid(row=1, column=0, sticky="nsew")
        self._activation_overlay.columnconfigure(0, weight=1)
        self._activation_overlay.rowconfigure(0, weight=1)
        
        # Create subpack selection overlay frame (hidden by default)
        self._subpack_overlay = _tk.Frame(self._root, bg='#0f1419')
        self._subpack_overlay.grid(row=1, column=0, sticky="nsew")
        self._subpack_overlay.columnconfigure(0, weight=1)
        self._subpack_overlay.rowconfigure(0, weight=1)
        self._subpack_overlay.grid_remove()  # Hide initially
        
        # Create version check overlay frame (hidden by default)
        self._version_check_overlay = _tk.Frame(self._root, bg='#0f1419')
        self._version_check_overlay.grid(row=1, column=0, sticky="nsew")
        self._version_check_overlay.columnconfigure(0, weight=1)
        self._version_check_overlay.rowconfigure(0, weight=1)
        self._version_check_overlay.grid_remove()  # Hide initially
        
        # Create ban screen overlay frame (hidden by default)
        self._ban_overlay = _tk.Frame(self._root, bg='#000000')
        self._ban_overlay.grid(row=1, column=0, sticky="nsew")
        self._ban_overlay.columnconfigure(0, weight=1)
        self._ban_overlay.rowconfigure(0, weight=1)
        self._ban_overlay.grid_remove()  # Hide initially
        
        # Create achievement status overlay frame (hidden by default)
        self._achievement_overlay = _tk.Frame(self._root, bg='#0f1419')
        self._achievement_overlay.grid(row=1, column=0, sticky="nsew")
        self._achievement_overlay.columnconfigure(0, weight=1)
        self._achievement_overlay.rowconfigure(0, weight=1)
        self._achievement_overlay.grid_remove()  # Hide initially
        
        # Create script API check overlay (Check Packs - script dependency grouping)
        self._script_api_overlay = _tk.Frame(self._root, bg='#0f1419')
        self._script_api_overlay.grid(row=1, column=0, sticky="nsew")
        self._script_api_overlay.columnconfigure(0, weight=1)
        self._script_api_overlay.rowconfigure(0, weight=1)
        self._script_api_overlay.grid_remove()  # Hide initially

        # Create identifier conflict resolution overlay (merge: choose which pack to keep per conflict)
        self._conflict_resolution_overlay = _tk.Frame(self._root, bg='#0f1419')
        self._conflict_resolution_overlay.grid(row=1, column=0, sticky="nsew")
        self._conflict_resolution_overlay.columnconfigure(0, weight=1)
        self._conflict_resolution_overlay.rowconfigure(0, weight=1)
        self._conflict_resolution_overlay.grid_remove()  # Hide initially
        
        # Create update-in-progress overlay (themed, like verification loading)
        self._update_overlay = _tk.Frame(self._root, bg='#000000')
        self._update_overlay.grid(row=1, column=0, sticky="nsew")
        self._update_overlay.columnconfigure(0, weight=1)
        self._update_overlay.rowconfigure(0, weight=1)
        self._update_overlay.grid_remove()  # Hide initially
        self._update_check_lock = threading.Lock()
        
        # Create Notebook for Tabs (hidden until activation)
        self.notebook = _ttk.Notebook(self._root)
        self.notebook.grid(row=1, column=0, sticky="nsew")
        self.notebook.grid_remove()  # Hide initially
        
        # Style the notebook tabs - pitch black, transparent look
        style = _ttk.Style()
        style.theme_use('clam')
        style.configure('TNotebook', background='#000000', borderwidth=0)
        style.configure('TNotebook.Tab', background='#000000', foreground='#888888', padding=[20, 10], borderwidth=0)
        style.map('TNotebook.Tab', background=[('selected', '#9333ea')], foreground=[('selected', '#FFFFFF')])

        # Create Frames for each Tab - pitch black background
        self.app1_frame = _tk.Frame(self.notebook, bg='#000000')
        self.mcpacker_frame = _tk.Frame(self.notebook, bg='#000000')
        self.list_maker_frame = _tk.Frame(self.notebook, bg='#000000')  # New List Maker Tab
        self.settings_frame = _tk.Frame(self.notebook, bg='#000000')
        self.help_frame = _tk.Frame(self.notebook, bg='#000000')

        # Adding Tabs to Notebook
        self.notebook.add(self.app1_frame, text=_("tabs.autobe"))
        self.notebook.add(self.mcpacker_frame, text=_("tabs.mcpacker"))
        self.notebook.add(self.list_maker_frame, text=_("tabs.list_maker"))
        self.notebook.add(self.help_frame, text=_("tabs.help"))
        
        # Add Settings as a special tab that shows dropdown instead of content
        self.notebook.add(self.settings_frame, text=_("tabs.settings"))
        
        # Bind to intercept Settings tab clicks BEFORE tab changes
        self.notebook.bind("<Button-1>", self._on_notebook_click)
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        # Configure resizing for the notebook's frames
        for frame in [self.app1_frame, self.mcpacker_frame, self.list_maker_frame, self.settings_frame, self.help_frame]:
            frame.columnconfigure(0, weight=1)
            frame.rowconfigure(0, weight=1)

        # Load settings and initialize mode selection variable
        loaded_settings = self._load_settings()
        self._current_lang = loaded_settings.get("lang", "en")
        self.mcpacker_mode_var = _tk.StringVar(value=loaded_settings.get("mcpacker_mode", "pack"))
        self.merge_by_version_var = _tk.BooleanVar(value=loaded_settings.get("merge_by_version", False))
        self.customize_pack_after_merge_var = _tk.BooleanVar(value=loaded_settings.get("customize_pack_after_merge", False))
        self.show_linked_packs_after_merge_var = _tk.BooleanVar(value=loaded_settings.get("show_linked_packs_after_merge", False))
        self.extendedbe_enabled_var = _tk.BooleanVar(value=loaded_settings.get("extendedbe_enabled", False))
        self.modpack_organization_var = _tk.BooleanVar(value=loaded_settings.get("modpack_organization", False))
        self.background_music_var = _tk.BooleanVar(value=loaded_settings.get("background_music", True))
        self.background_music_volume_var = _tk.IntVar(value=min(100, max(0, loaded_settings.get("background_music_volume", 70))))
        self.music_shuffle_var = _tk.BooleanVar(value=loaded_settings.get("music_shuffle", True))
        self.music_playlist_var = _tk.StringVar(value=loaded_settings.get("music_playlist", "__all__"))
        
        # Add trace to save settings whenever the variable changes
        self.mcpacker_mode_var.trace_add('write', lambda *args: self._save_settings())
        self.merge_by_version_var.trace_add('write', lambda *args: self._save_settings())
        self.customize_pack_after_merge_var.trace_add('write', lambda *args: self._save_settings())
        self.show_linked_packs_after_merge_var.trace_add('write', lambda *args: self._save_settings())
        self.extendedbe_enabled_var.trace_add('write', lambda *args: self._save_settings())
        self.modpack_organization_var.trace_add('write', lambda *args: self._save_settings())
        def _on_background_music_var_change(*args):
            self._save_settings()
            if getattr(self, '_root', None) and self._root.winfo_exists():
                self._root.after(0, self._apply_background_music_setting)
        self.background_music_var.trace_add('write', _on_background_music_var_change)
        def _on_background_music_volume_change(*args):
            self._save_settings()
            if getattr(self, '_root', None) and self._root.winfo_exists():
                self._root.after(0, self._apply_background_music_volume)
            try:
                lbl = getattr(self, "_settings_vol_value_label", None)
                if lbl is not None and lbl.winfo_exists():
                    lbl.config(text=str(getattr(self, "background_music_volume_var", _tk.IntVar(value=70)).get()) + "%")
            except Exception:
                pass
        self.background_music_volume_var.trace_add('write', _on_background_music_volume_change)
        def _on_music_shuffle_var_change(*args):
            self._save_settings()
            self._on_music_shuffle_setting_changed()
        self.music_shuffle_var.trace_add('write', _on_music_shuffle_var_change)
        def _on_music_playlist_var_change(*args):
            self._save_settings()
            self._on_music_playlist_setting_changed()
        self.music_playlist_var.trace_add('write', _on_music_playlist_var_change)

        # Initialize Settings Tab first (so mode is available for MCPACKER)
        self.init_settings_tab()

        # Initialize MCPACKER Tab Content
        self.init_mcpacker_tab()

        # Initialize List Maker Tab Content
        self.init_list_maker_tab()

        # Initialize Help Tab Content
        self.init_help_tab()
        
        # Track loading state for close protection
        self._is_loading = False
        
        # Initialize Discord Rich Presence (optional) — deferred, then run in thread so pipe tries don't freeze UI
        self.discord_rpc = None
        self._root.after(500, lambda: threading.Thread(target=self._init_discord_rpc, daemon=True).start())
        
        # Bind tab change event - handled by _on_settings_tab_click which also calls _on_tab_changed
        # _on_settings_tab_click will handle Settings tab specially
        
        # Set up window close protocol handler
        self._original_protocol = None
        self._root.protocol("WM_DELETE_WINDOW", self._on_window_close)
        
        # Defer activation until UI is ready to avoid root destruction errors
        self._root.after(0, self._check_activation)

    def _find_app_icon_paths(self):
        """Return candidate icon paths in priority order."""
        return _get_app_icon_paths()

    def _apply_window_icon(self, window):
        """Apply branded app icon to a Tk/Toplevel window."""
        _apply_window_icon_global(window)

    def _init_custom_title_bar(self):
        """Create dark custom title bar with drag/min/max/close controls."""
        self._titlebar = _tk.Frame(self._root, bg="#000000", height=34, highlightthickness=1, highlightbackground="#1f1f1f")
        self._titlebar.grid(row=0, column=0, sticky="ew")
        self._titlebar.grid_columnconfigure(1, weight=1)
        self._titlebar.grid_propagate(False)

        self._main_title_icon_img = _get_titlebar_icon_image(14)
        if self._main_title_icon_img is not None:
            title_icon = _tk.Label(self._titlebar, image=self._main_title_icon_img, bg="#000000")
        else:
            title_icon = _tk.Label(self._titlebar, text="◈", bg="#000000", fg="#9333ea", font=("Segoe UI", 10, "bold"))
        title_icon.grid(row=0, column=0, padx=(8, 6), sticky="w")
        self._title_text = _tk.Label(self._titlebar, text="AutoBE - CodeNex", bg="#000000", fg="#E5E7EB", font=("Segoe UI", 10))
        self._title_text.grid(row=0, column=1, sticky="w")

        btns = _tk.Frame(self._titlebar, bg="#000000")
        btns.grid(row=0, column=2, sticky="e")

        self._btn_min = _tk.Button(btns, text="—", command=self._window_minimize, bg="#000000", fg="#E5E7EB",
                                   font=("Segoe UI", 10, "bold"), relief="flat", bd=0, padx=12, pady=3,
                                   activebackground="#1f1f1f", activeforeground="#FFFFFF", cursor="hand2")
        self._btn_min.pack(side="left")
        self._btn_max = _tk.Button(btns, text="□", command=self._window_toggle_maximize, bg="#000000", fg="#E5E7EB",
                                   font=("Segoe UI", 10, "bold"), relief="flat", bd=0, padx=12, pady=3,
                                   activebackground="#1f1f1f", activeforeground="#FFFFFF", cursor="hand2")
        self._btn_max.pack(side="left")
        self._btn_close = _tk.Button(btns, text="✕", command=self._window_close, bg="#000000", fg="#E5E7EB",
                                     font=("Segoe UI", 10, "bold"), relief="flat", bd=0, padx=12, pady=3,
                                     activebackground="#c42b1c", activeforeground="#FFFFFF", cursor="hand2")
        self._btn_close.pack(side="left")

        for w in (self._titlebar, title_icon, self._title_text):
            w.bind("<ButtonPress-1>", self._window_drag_start, add="+")
            w.bind("<B1-Motion>", self._window_drag_move, add="+")
            w.bind("<Double-Button-1>", lambda e: self._window_toggle_maximize(), add="+")

        # Re-apply borderless mode after minimize/restore.
        self._root.bind("<Map>", self._window_on_map, add="+")

    def _window_drag_start(self, event):
        if self._is_maximized:
            return
        self._drag_offset_x = event.x_root - self._root.winfo_x()
        self._drag_offset_y = event.y_root - self._root.winfo_y()

    def _window_drag_move(self, event):
        if self._is_maximized:
            return
        x = event.x_root - self._drag_offset_x
        y = event.y_root - self._drag_offset_y
        self._root.geometry(f"+{x}+{y}")

    def _window_toggle_maximize(self):
        try:
            if not self._is_maximized:
                self._restore_geometry = self._root.geometry()
                sw = self._root.winfo_screenwidth()
                sh = self._root.winfo_screenheight()
                self._root.geometry(f"{sw}x{sh}+0+0")
                self._is_maximized = True
                self._btn_max.config(text="❐")
            else:
                if self._restore_geometry:
                    self._root.geometry(self._restore_geometry)
                self._is_maximized = False
                self._btn_max.config(text="□")
        except Exception:
            pass

    def _window_minimize(self):
        try:
            self._root.overrideredirect(False)
            self._root.iconify()
        except Exception:
            pass

    def _window_on_map(self, event=None):
        try:
            if self._root.state() != "iconic":
                self._root.overrideredirect(True)
        except Exception:
            pass

    def _window_close(self):
        try:
            self._on_window_close()
        except Exception:
            try:
                self._root.destroy()
            except Exception:
                pass

    def _init_discord_rpc(self):
        """Initialize Discord Rich Presence. Tries pipes 0-9; fails silently if Discord not running or pypresence missing."""
        if not getattr(self, "_root", None) or not self._root.winfo_exists():
            return
        self.discord_rpc = None
        presence_cls = Presence
        if presence_cls is None and getattr(sys, "frozen", False):
            try:
                from pypresence import Presence as _P  # type: ignore[import-untyped]
                presence_cls = _P
            except Exception:
                presence_cls = None
        if not DISCORD_RPC_AVAILABLE and presence_cls is None:
            return
        if presence_cls is None:
            return
        CLIENT_ID = "1304230074513358929"
        last_err = None
        for pipe in range(10):
            try:
                try:
                    rpc = presence_cls(CLIENT_ID, pipe=pipe, instance=False)
                except TypeError:
                    rpc = presence_cls(CLIENT_ID, instance=False)
                if not hasattr(rpc, "connect"):
                    continue
                rpc.connect()
                # First update must be on same thread as connect (some Discord clients drop it otherwise)
                try:
                    rpc.update(
                        details="Using AutoBE",
                        state="Ready • © CodeNex 2024",
                        large_image="autobediscord",
                        large_text="AutoBE - CodeNex",
                        start=int(_datetime.datetime.now().timestamp())
                    )
                except Exception:
                    try:
                        rpc.update(details="Using AutoBE", state="Ready • © CodeNex 2024")
                    except Exception:
                        pass
                self.discord_rpc = rpc
                # Schedule periodic refresh so Discord keeps showing presence (stops dropping after idle)
                if self._is_root_alive():
                    self._schedule_discord_refresh()
                return
            except Exception as e:
                last_err = e
                continue
        self.discord_rpc = None
        _logging.debug("Discord RPC failed (tried pipes 0-9): %s", last_err)
        _logging.info("Discord RPC unavailable (Discord may be closed): %s", last_err)

    # Rotating idle status pool — cycles every 45 s refresh
    _DISCORD_IDLE_POOL = [
        ("Building the ultimate modpack",      "In the lab"),
        ("Addon engineer on standby",           "Waiting to merge"),
        ("Making Bedrock hit different",        "AutoBE loaded & ready"),
        ("100+ addons? No problem",             "Merge wizard online"),
        ("Deep in the modpack trenches",         "Precision mode"),
        ("The modpack won't build itself",      "Get to work"),
        ("Every addon. One pack.",              "That's the AutoBE way"),
        ("Pushing Bedrock to its limits",       "Next-gen tooling"),
        ("Merge, deploy, repeat",               "Powered by CodeNex"),
        ("Crafting something legendary",        "Stay tuned"),
        ("Stress-testing 118 addons",           "Still not breaking a sweat"),
        ("Constructing the impossible pack",    "Brick by brick"),
        ("Packs sorted. Conflicts resolved.",   "AutoBE in session"),
        ("Bedrock edition, elevated",           "CodeNex ecosystem"),
        ("Future of Bedrock modding",           "You're early"),
    ]

    def _schedule_discord_refresh(self):
        """Re-send presence every 45s so Discord doesn't drop it. Cancelled on close."""
        if not getattr(self, "_root", None) or not self._root.winfo_exists():
            return
        # If Discord RPC failed to initialize, retry every 30 seconds
        if not self.discord_rpc:
            if getattr(self, "_root", None) and self._root.winfo_exists():
                self._discord_refresh_id = self._root.after(30000, self._schedule_discord_refresh)
                # Try to initialize Discord RPC again
                threading.Thread(target=self._init_discord_rpc, daemon=True).start()
            return
        # Don't stomp live merge status with idle rotating messages
        if not getattr(self, "_discord_merging", False):
            try:
                self._discord_idle_index = (getattr(self, "_discord_idle_index", -1) + 1) % len(self._DISCORD_IDLE_POOL)
                self._update_discord_presence()
            except Exception:
                self._update_discord_presence()
        if getattr(self, "_root", None) and self._root.winfo_exists():
            self._discord_refresh_id = self._root.after(45000, self._schedule_discord_refresh)

    def _set_discord_merge_step(self, details, state):
        """Immediately push a merge-step status to Discord (no self-imposed rate limit)."""
        if not self.discord_rpc or not hasattr(self.discord_rpc, "update"):
            return
        state_str = f"{state} \u2022 \u00a9 CodeNex 2025"
        try:
            self.discord_rpc.update(
                details=details,
                state=state_str,
                large_image="autobediscord",
                large_text="AutoBE by CodeNex",
                start=getattr(self, "_merge_discord_start", int(_datetime.datetime.now().timestamp()))
            )
        except Exception:
            try:
                self.discord_rpc.update(details=details, state=state_str)
            except Exception:
                pass
    
    def _update_discord_presence(self, details=None, state=None, tab_name=None):
        """Update Discord Rich Presence status. No-op if RPC is unavailable or update fails."""
        if not self.discord_rpc or not hasattr(self.discord_rpc, "update"):
            return
        try:
            # Check if Minecraft is running
            minecraft_running = self._is_minecraft_running()
            
            if details is None and state is None and tab_name is None:
                # Rotating idle pool — pick current index set by _schedule_discord_refresh
                idx = getattr(self, "_discord_idle_index", 0) % len(self._DISCORD_IDLE_POOL)
                details, state = self._DISCORD_IDLE_POOL[idx]
            elif tab_name:
                _tab_map = {
                    "AutoBE":     ("AutoBE — Addon Forge",   "Building the modpack"),
                    "MCPACKER":   ("MCPACKER — Pack Tools",  "Converting formats"),
                    "List Maker": ("List Maker — Planning", "Creating pack lists"),
                    "Help":       ("AutoBE — Documentation", "Learning the ropes"),
                }
                details, state = _tab_map.get(tab_name, ("AutoBE", "Idle"))
            
            # If Minecraft is running, show both activities
            if minecraft_running:
                if details and not details.startswith("Minecraft + "):
                    details = f"Minecraft + {details}"
                elif not details:
                    details = "Minecraft + AutoBE"
            
            # Add current song to state if music is playing
            current_song = getattr(self, "_current_track_name", None)
            if current_song:
                state = f"{state} • 🎵 {current_song}"
            
            state_str = f"{state} • © CodeNex 2025"
            try:
                self.discord_rpc.update(
                    details=details,
                    state=state_str,
                    large_image="autobediscord",
                    large_text="AutoBE by CodeNex",
                    start=int(_datetime.datetime.now().timestamp())
                )
            except Exception:
                try:
                    self.discord_rpc.update(details=details, state=state_str)
                except Exception as e2:
                    raise e2
        except Exception as e:
            _logging.debug("Discord RPC update failed: %s", e)
            self.discord_rpc = None
            _logging.info("Discord RPC disconnected; continuing without presence.")
    
    def _update_discord_merge_progress(self, pack_name, current, total, merge_start_ts):
        """Update Discord RPC to show live merge progress. Rate-limited to once per 15 s."""
        if not self.discord_rpc or not hasattr(self.discord_rpc, "update"):
            return
        now = _time.monotonic()
        last = getattr(self, "_discord_merge_last_update", 0)
        if now - last < 15:
            return
        self._discord_merge_last_update = now
        short = pack_name if len(pack_name) <= 40 else pack_name[:37] + "..."
        try:
            state_str = f"Pack {current}/{total} \u2014 {short} \u2022 \u00a9 CodeNex 2024"
            try:
                self.discord_rpc.update(
                    details=f"Merging {total} addons...",
                    state=state_str,
                    large_image="autobediscord",
                    large_text="AutoBE - CodeNex",
                    start=merge_start_ts
                )
            except Exception:
                self.discord_rpc.update(
                    details=f"Merging {total} addons...",
                    state=state_str
                )
        except Exception as e:
            _logging.debug("Discord RPC merge update failed: %s", e)

    def _on_tab_changed(self, event=None):
        """Called when user switches tabs - update Discord presence and close settings dropdown."""
        if not self._is_root_alive():
            return
        
        try:
            # Close settings dropdown if open when switching tabs
            if hasattr(self, '_settings_dropdown'):
                try:
                    if self._settings_dropdown.winfo_exists():
                        self._close_settings_dropdown()
                except:
                    pass
            
            selected_tab = self.notebook.index(self.notebook.select())
            # Tab order: AutoBE=0, MCPACKER=1, List Maker=2, Help=3, Settings=4
            tab_names = [_("tabs.autobe"), _("tabs.mcpacker"), _("tabs.list_maker"), _("tabs.help"), _("tabs.settings")]
            if 0 <= selected_tab < len(tab_names) and selected_tab != 4:  # Skip Settings tab
                self._update_discord_presence(tab_name=tab_names[selected_tab])
        except Exception:
            pass
    
    
    def _close_discord_rpc(self):
        """Close Discord Rich Presence connection."""
        try:
            if getattr(self, "_discord_refresh_id", None) and getattr(self, "_root", None) and self._root.winfo_exists():
                self._root.after_cancel(self._discord_refresh_id)
        except Exception:
            pass
        self._discord_refresh_id = None
        if not self.discord_rpc:
            return
        try:
            # Clear the activity first so Discord removes the presence immediately
            if hasattr(self.discord_rpc, "clear"):
                self.discord_rpc.clear()
        except Exception:
            pass
        try:
            if hasattr(self.discord_rpc, "close"):
                self.discord_rpc.close()
        except Exception:
            pass
        self.discord_rpc = None
    
    def _is_root_alive(self):
        """Safely check if root window exists without raising exceptions."""
        try:
            return self._root and self._root.winfo_exists()
        except (_tk.TclError, RuntimeError):
            return False
    
    def _is_pack_obfuscated(self, file_path):
            """Checks if a pack contains closed-source/obfuscated JSON files."""
            try:
                with _zipfile.ZipFile(file_path, 'r') as pack:
                    for name in pack.namelist():
                        if name.endswith('.json'):
                            with pack.open(name) as f:
                                try:
                                    # Read the beginning of the file to check for protection markers
                                    raw = f.read(2048).decode('utf-8', errors='ignore').strip()
                                    # Marker 1: Starts with */ (illegal JSON syntax used for protection)
                                    # Marker 2: High density of Unicode escapes (\u0065 format)
                                    if raw.startswith('*/') or len(_re.findall(r'\\u[0-9a-fA-F]{4}', raw)) > 15:
                                        return True
                                except:
                                    continue
            except:
                pass
            return False

    def _on_window_close(self):
        """Handle window close attempts - prevent closing during loading."""
        if self._is_loading:
            self._show_close_warning()
        else:
            # Close Discord RPC connection
            self._close_discord_rpc()
            self._root.destroy()
    
    def _show_close_warning(self):
        """Show warning overlay in the main window when user tries to close during loading."""
        if not self._is_root_alive():
            return
        
        # Create warning overlay frame (on top of loading overlay)
        if not hasattr(self, '_warning_overlay'):
            self._warning_overlay = _tk.Frame(self._root, bg='#0A0A0A')
            self._warning_overlay.grid(row=0, column=0, sticky="nsew")
            self._warning_overlay.columnconfigure(0, weight=1)
            self._warning_overlay.rowconfigure(0, weight=1)
        else:
            # Clear existing widgets
            for widget in self._warning_overlay.winfo_children():
                widget.destroy()
        
        # Create centered container
        center_frame = _tk.Frame(self._warning_overlay, bg='#0A0A0A')
        center_frame.place(relx=0.5, rely=0.5, anchor='center')
        
        # Warning icon (using emoji for modern look)
        icon_label = _tk.Label(
            center_frame,
            text="⚠️",
            bg='#0A0A0A',
            fg='#FFAA00',
            font=("Helvetica", 48)
        )
        icon_label.pack(pady=(0, 20))
        
        # Title
        title_label = _tk.Label(
            center_frame,
            text=_("activation.in_progress"),
            bg='#0A0A0A',
            fg='#E1E1E1',
            font=("Helvetica", 18, "bold")
        )
        title_label.pack(pady=(0, 15))
        
        # Message
        message_label = _tk.Label(
            center_frame,
            text=_("activation.please_wait"),
            bg='#0A0A0A',
            fg='#CCCCCC',
            font=("Helvetica", 11),
            justify=_tk.CENTER
        )
        message_label.pack(pady=(0, 25))
        
        # Button container
        button_frame = _tk.Frame(center_frame, bg='#0A0A0A')
        button_frame.pack()
        
        # Continue button (hides warning, returns to loading)
        continue_button = _tk.Button(
            button_frame,
            text=_("activation.continue_waiting"),
            command=self._hide_close_warning,
            bg='#A50CAC',
            fg='#FFFFFF',
            font=("Helvetica", 11, "bold"),
            relief=_tk.FLAT,
            bd=0,
            cursor="hand2",
            activebackground='#8B0A9C',
            activeforeground='#FFFFFF',
            padx=30,
            pady=10,
            width=15
        )
        continue_button.pack()
        
        # Show the warning overlay (on top)
        self._warning_overlay.tkraise()
        
        # Bind Enter and Escape keys
        self._root.bind('<Return>', lambda e: self._hide_close_warning())
        self._root.bind('<Escape>', lambda e: self._hide_close_warning())
    
    def _hide_close_warning(self):
        """Hide warning overlay and return to loading screen."""
        if hasattr(self, '_warning_overlay'):
            self._warning_overlay.grid_remove()
        # Return to loading overlay (which should still be visible underneath)
        if hasattr(self, '_activation_overlay'):
            self._activation_overlay.tkraise()
        # Unbind keys
        self._root.unbind('<Return>')
        self._root.unbind('<Escape>')

    def _get_app_directory(self):
        """Get the directory where the executable/script is located."""
        if getattr(sys, 'frozen', False):
            # Running as compiled executable (PyInstaller)
            app_dir = _os.path.dirname(sys.executable)
        else:
            # Running as script
            app_dir = _os.path.dirname(_os.path.abspath(__file__))
        return app_dir
    
    def _get_settings_path(self):
        """Get the path to the settings file."""
        app_dir = self._get_app_directory()
        cache_dir = _os.path.join(app_dir, ".autobe")
        try:
            _os.makedirs(cache_dir, exist_ok=True)
        except Exception as e:
            log_error(f"Failed to create settings directory: {e}")
        return _os.path.join(cache_dir, "settings.be")

    # Internal storage: obscure names and encoded content so users don't see "hwid"/"blacklist" or raw data.
    _AB_VERIFIED_FILE = ".ab"
    _AB_CACHE_FILE = ".ac"
    _AB_FINGERPRINT_FILE = ".af"

    def _get_verified_hwids_path(self):
        """Internal path for verified device state (not user-visible)."""
        cache_dir = _os.path.dirname(self._get_settings_path())
        return _os.path.join(cache_dir, self._AB_VERIFIED_FILE)

    def _get_blacklist_cache_path(self):
        """Internal path for block cache (not user-visible)."""
        cache_dir = _os.path.dirname(self._get_settings_path())
        return _os.path.join(cache_dir, self._AB_CACHE_FILE)

    def _get_fingerprint_store_path(self):
        """Internal path for device fingerprint binding (HWID -> fingerprint hash)."""
        cache_dir = _os.path.dirname(self._get_settings_path())
        return _os.path.join(cache_dir, self._AB_FINGERPRINT_FILE)

    def _clear_local_cache_files(self):
        """Clear all local cache files to fix false bans on reinstall.
        Only clears if version changed (indicates update/reinstall), not every launch."""
        cache_dir = _os.path.dirname(self._get_settings_path())
        version_file = _os.path.join(cache_dir, ".av")  # AutoBE Version file

        # Check if this is a new version (reinstall/update)
        current_version = APP_VERSION
        stored_version = None
        try:
            if _os.path.isfile(version_file):
                with open(version_file, "r", encoding="utf-8") as f:
                    stored_version = f.read().strip()
        except Exception:
            pass

        # Only clear cache if version changed (reinstall/update) or no version file (first install)
        if stored_version is None or stored_version != current_version:
            cache_files = [
                self._AB_VERIFIED_FILE,
                self._AB_CACHE_FILE,
                self._AB_FINGERPRINT_FILE
            ]
            cleared = []
            for filename in cache_files:
                path = _os.path.join(cache_dir, filename)
                if _os.path.isfile(path):
                    try:
                        _os.remove(path)
                        cleared.append(filename)
                    except Exception as e:
                        _logging.debug(f"Failed to clear cache file {filename}: {e}")
            if cleared:
                _logging.info(f"Cleared local cache files on version change ({stored_version} -> {current_version}): {cleared}")

            # Update stored version
            try:
                _os.makedirs(cache_dir, exist_ok=True)
                with open(version_file, "w", encoding="utf-8") as f:
                    f.write(current_version)
            except Exception:
                pass

    @staticmethod
    def _block_hash(hwid):
        """One-way hash so we never store actual IDs locally (verified or blocked). Cannot be reversed to get ID."""
        return hashlib.sha256((hwid or "").strip().encode("utf-8")).hexdigest()

    def _set_file_hidden_if_windows(self, path):
        """Set file hidden on Windows so it doesn't show in normal folder view."""
        try:
            if platform.system() == "Windows" and _os.path.isfile(path):
                _ctypes.windll.kernel32.SetFileAttributesW(path, 0x02)  # FILE_ATTRIBUTE_HIDDEN
        except Exception:
            pass

    def _load_verified_hwids(self):
        """Load set of hashes only — no actual IDs stored. For offline check we match current device by hash."""
        path = self._get_verified_hwids_path()
        out = set()
        try:
            if _os.path.isfile(path):
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        # New format: 64-char hex (SHA256) — no ID, cannot be reversed
                        if len(line) == 64 and all(c in "0123456789abcdef" for c in line.lower()):
                            out.add(line.lower())
                        else:
                            # Old format: base64 ID — hash it and keep only hash
                            try:
                                decoded = base64.b64decode(line).decode("utf-8", errors="ignore").strip()
                                if decoded:
                                    out.add(self._block_hash(decoded))
                            except Exception:
                                pass
            # Migrate from old plain-text file if present (one-time)
            old_path = _os.path.join(_os.path.dirname(path), "verified_hwids.txt")
            if _os.path.isfile(old_path) and not out:
                with open(old_path, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        h = line.strip()
                        if h:
                            out.add(self._block_hash(h))
                try:
                    _os.makedirs(_os.path.dirname(path), exist_ok=True)
                    with open(path, "w", encoding="utf-8") as g:
                        for h in out:
                            g.write(h + "\n")
                    self._set_file_hidden_if_windows(path)
                    _os.remove(old_path)
                except Exception:
                    pass
        except Exception:
            pass
        return out

    def _save_verified_hwid(self, hwid):
        """Save this device as verified (only when activated online). Only a one-way hash is stored — no ID visible."""
        if not hwid or not hwid.strip():
            return
        hwid = hwid.strip()
        path = self._get_verified_hwids_path()
        try:
            h = self._block_hash(hwid)
            existing = self._load_verified_hwids()
            if h in existing:
                return
            _os.makedirs(_os.path.dirname(path), exist_ok=True)
            with open(path, "a", encoding="utf-8") as f:
                f.write(h + "\n")
            self._set_file_hidden_if_windows(path)
        except Exception as e:
            _logging.debug("Save verified state failed: %s", e)

    def _remove_verified_hwid(self, hwid):
        """Remove this device from local verified (e.g. when online and no longer on GitHub whitelist). Keeps offline in sync with GitHub."""
        if not hwid or not hwid.strip():
            return
        path = self._get_verified_hwids_path()
        try:
            existing = self._load_verified_hwids()
            existing.discard(self._block_hash(hwid.strip()))
            _os.makedirs(_os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                for h in existing:
                    f.write(h + "\n")
            self._set_file_hidden_if_windows(path)
        except Exception as e:
            _logging.debug("Remove verified state failed: %s", e)

    def _get_device_fingerprint(self):
        """Stable hardware fingerprint (hash) for this machine. Used to detect HWID spoofing: same HWID on different hardware = different fingerprint."""
        parts = []
        try:
            if platform.system() == "Windows":
                try:
                    out = subprocess.check_output(
                        ["wmic", "baseboard", "get", "serialnumber"],
                        stderr=subprocess.STDOUT, text=True, timeout=5
                    )
                    serial = next((l.strip().lower() for l in out.splitlines() if l.strip() and "serialnumber" not in l.lower()), "")
                    parts.append(serial or "?")
                except Exception:
                    parts.append("?")
                try:
                    out = subprocess.check_output(
                        ["wmic", "cpu", "get", "processorid"],
                        stderr=subprocess.STDOUT, text=True, timeout=5
                    )
                    pid = next((l.strip().lower() for l in out.splitlines() if l.strip() and "processorid" not in l.lower()), "")
                    parts.append(pid or "?")
                except Exception:
                    parts.append("?")
                try:
                    out = subprocess.check_output(
                        ["wmic", "diskdrive", "get", "serialnumber"],
                        stderr=subprocess.STDOUT, text=True, timeout=5
                    )
                    serials = [l.strip().lower() for l in out.splitlines() if l.strip() and "serialnumber" not in l.lower()]
                    parts.append("|".join(serials) if serials else "?")
                except Exception:
                    parts.append("?")
                try:
                    out = subprocess.check_output(
                        ["wmic", "bios", "get", "version"],
                        stderr=subprocess.STDOUT, text=True, timeout=5
                    )
                    ver = next((l.strip().lower() for l in out.splitlines() if l.strip() and "version" not in l.lower()), "")
                    parts.append(ver or "?")
                except Exception:
                    parts.append("?")
            elif platform.system() == "Linux":
                try:
                    with open("/etc/machine-id", "r", encoding="utf-8", errors="ignore") as f:
                        parts.append(f.read().strip() or "?")
                except Exception:
                    parts.append(platform.node() or "?")
                for name in ["product_uuid", "product_serial", "board_serial"]:
                    try:
                        path = _os.path.join("/sys/class/dmi/id", name)
                        if _os.path.isfile(path):
                            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                                parts.append(f.read().strip() or "?")
                            break
                    except Exception:
                        pass
                if len(parts) < 2:
                    parts.append(platform.node() or "?")
            elif platform.system() == "Darwin":
                try:
                    out = subprocess.check_output(
                        ["system_profiler", "SPHardwareDataType"],
                        stderr=subprocess.DEVNULL, text=True, timeout=10
                    )
                    for line in out.splitlines():
                        if "Serial Number" in line or "Hardware UUID" in line:
                            parts.append(line.strip().lower())
                    if not parts:
                        parts.append(platform.node() or "?")
                except Exception:
                    parts.append(platform.node() or "?")
            else:
                parts.append(platform.node() or "?")
        except Exception:
            parts.append(platform.node() or "?")
        raw = "|".join(parts) if parts else platform.node() or "fp"
        return hashlib.sha256(raw.encode("utf-8", errors="replace")).hexdigest()

    def _load_fingerprint_store(self):
        """Load HWID hash -> fingerprint hash map (one binding per HWID, first activation wins)."""
        path = self._get_fingerprint_store_path()
        out = {}
        try:
            if _os.path.isfile(path):
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        line = line.strip()
                        if not line or "\t" not in line and " " not in line:
                            continue
                        sep = "\t" if "\t" in line else " "
                        a, b = line.split(sep, 1)
                        a, b = a.strip().lower(), b.strip().lower()
                        if len(a) == 64 and len(b) == 64 and all(c in "0123456789abcdef" for c in a + b):
                            out[a] = b
        except Exception:
            pass
        return out

    def _save_fingerprint_for_hwid(self, hwid_hash, fingerprint_hash):
        """Store fingerprint for this HWID only if not already set (first device to activate with this HWID is the bound device)."""
        if not hwid_hash or not fingerprint_hash or len(hwid_hash) != 64 or len(fingerprint_hash) != 64:
            return
        path = self._get_fingerprint_store_path()
        try:
            store = self._load_fingerprint_store()
            if hwid_hash in store:
                return
            store[hwid_hash] = fingerprint_hash
            _os.makedirs(_os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                for h, fp in store.items():
                    f.write(h + " " + fp + "\n")
            self._set_file_hidden_if_windows(path)
        except Exception as e:
            _logging.debug("Save fingerprint binding failed: %s", e)

    def _get_stored_fingerprint(self, hwid_hash):
        """Return stored fingerprint hash for this HWID, or None if never bound."""
        store = self._load_fingerprint_store()
        return store.get(hwid_hash)

    def _deny_and_blacklist_spoofed_hwid(self, _hwid, reason="Device binding mismatch (HWID may be spoofed)."):
        """Remove from verified, add to blacklist (GitHub + cache), show denied. All automatic."""
        self._remove_verified_hwid(_hwid)
        try:
            self._append_to_blacklist(_hwid)
        except Exception as e:
            log_error(f"Failed to add spoofed HWID to blacklist: {e}")
        self._append_to_blacklist_cache(_hwid)
        denied_message = f"{reason}\nAccess denied."
        if self._is_root_alive():
            try:
                self._root.deiconify()
                self._root.update_idletasks()
            except Exception:
                pass
            self._root.after(100, lambda: self._show_denied_screen(denied_message))
        else:
            _messagebox.showerror(_("msg.spoofer_detected"), denied_message)
            sys.exit()

    def _load_cached_blacklist(self):
        """Load cached block list as set of hashes only. No actual IDs stored — users can't get blocked IDs."""
        path = self._get_blacklist_cache_path()
        out = set()
        try:
            had_old_format = False
            if _os.path.isfile(path):
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        # New format: 64-char hex (SHA256 hash) — no ID, cannot be reversed
                        if len(line) == 64 and all(c in "0123456789abcdef" for c in line.lower()):
                            out.add(line.lower())
                        else:
                            # Old format: base64-encoded ID — hash it and keep only the hash
                            had_old_format = True
                            try:
                                decoded = base64.b64decode(line).decode("utf-8", errors="ignore").strip()
                                if decoded:
                                    out.add(self._block_hash(decoded))
                            except Exception:
                                pass
            # Migrate from old plain-text file if present (one-time)
            old_path = _os.path.join(_os.path.dirname(path), "blacklist_cache.txt")
            if _os.path.isfile(old_path) and not out:
                with open(old_path, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        h = line.strip()
                        if h:
                            out.add(self._block_hash(h))
                had_old_format = True
                try:
                    _os.makedirs(_os.path.dirname(path), exist_ok=True)
                    with open(path, "w", encoding="utf-8") as g:
                        for h in out:
                            g.write(h + "\n")
                    self._set_file_hidden_if_windows(path)
                    _os.remove(old_path)
                except Exception:
                    pass
            # If file had old format (IDs), re-save as hashes only so no ID is ever stored
            if had_old_format and out:
                try:
                    _os.makedirs(_os.path.dirname(path), exist_ok=True)
                    with open(path, "w", encoding="utf-8") as g:
                        for h in out:
                            g.write(h + "\n")
                    self._set_file_hidden_if_windows(path)
                except Exception:
                    pass
        except Exception:
            pass
        return out

    def _save_blacklist_cache(self, blacklist_text):
        """Save block list as hashes only when we fetch from GitHub. No actual IDs written — users never see blocked IDs."""
        if not blacklist_text or not blacklist_text.strip():
            return
        path = self._get_blacklist_cache_path()
        try:
            _os.makedirs(_os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                for line in blacklist_text.strip().splitlines():
                    line = line.strip()
                    if line:
                        f.write(self._block_hash(line) + "\n")
            self._set_file_hidden_if_windows(path)
        except Exception as e:
            _logging.debug("Save cache failed: %s", e)

    def _append_to_blacklist_cache(self, hwid):
        """Add a blocked device by hash only. The actual ID is never stored — users can't get it."""
        if not hwid or not hwid.strip():
            return
        h = self._block_hash(hwid)
        path = self._get_blacklist_cache_path()
        try:
            existing = self._load_cached_blacklist()
            if h in existing:
                return
            _os.makedirs(_os.path.dirname(path), exist_ok=True)
            with open(path, "a", encoding="utf-8") as f:
                f.write(h + "\n")
            self._set_file_hidden_if_windows(path)
        except Exception as e:
            _logging.debug("Append to cache failed: %s", e)

    def _ensure_music_credits_file(self):
        """Copy MUSIC_CREDITS.txt into the user's .autobe folder so they have the credit link (YouTube) after install."""
        try:
            settings_path = self._get_settings_path()
            cache_dir = _os.path.dirname(settings_path)
            source = _os.path.join(getattr(sys, '_MEIPASS', _BASE_DIR), 'MUSIC_CREDITS.txt')
            if not _os.path.isfile(source):
                source = _os.path.join(_BASE_DIR, 'MUSIC_CREDITS.txt')
            if not _os.path.isfile(source):
                return
            dest = _os.path.join(cache_dir, 'MUSIC_CREDITS.txt')
            if _os.path.isfile(dest):
                return
            _shutil.copy2(source, dest)
        except Exception:
            pass
    
    def _load_settings(self):
        """Load settings from file."""
        settings_path = self._get_settings_path()
        default_settings = {
            "mcpacker_mode": "pack",
            "lang": "en",
            "merge_by_version": False,
            "customize_pack_after_merge": False,
            "show_linked_packs_after_merge": False,
            "background_music": True,
            "background_music_volume": 70,
            "music_shuffle": True,
            "music_playlist": "__all__",
            "auto_import": False,
            "mc_path": "",
            "extendedbe_enabled": False
        }
        try:
            if _os.path.exists(settings_path):
                with open(settings_path, 'r', encoding='utf-8') as f:
                    loaded = _json.load(f)
                    # Merge with defaults to ensure all settings exist
                    default_settings.update(loaded)
            return default_settings
        except Exception as e:
            log_error(f"Failed to load settings: {e}")
            return default_settings
    
    def _save_settings(self, *args):
        """Save current settings to file."""
        # Prevent saving during initialization
        if not hasattr(self, 'mcpacker_mode_var') or not hasattr(self, 'merge_by_version_var'):
            return
        
        settings_path = self._get_settings_path()
        try:
            settings = {
                "mcpacker_mode": self.mcpacker_mode_var.get(),
                "lang": getattr(self, "_current_lang", "en"),
                "merge_by_version": getattr(self, "merge_by_version_var", _tk.BooleanVar(value=False)).get(),
                "customize_pack_after_merge": getattr(self, "customize_pack_after_merge_var", _tk.BooleanVar(value=False)).get(),
                "show_linked_packs_after_merge": getattr(self, "show_linked_packs_after_merge_var", _tk.BooleanVar(value=False)).get(),
                "background_music": getattr(self, "background_music_var", _tk.BooleanVar(value=True)).get(),
                "background_music_volume": getattr(self, "background_music_volume_var", _tk.IntVar(value=70)).get(),
                "music_shuffle": getattr(self, "music_shuffle_var", _tk.BooleanVar(value=True)).get(),
                "music_playlist": getattr(self, "music_playlist_var", _tk.StringVar(value="__all__")).get(),
                "auto_import": getattr(self, "_auto_import_var", _tk.BooleanVar(value=False)).get(),
                "mc_path": getattr(self, "_mc_path_var", _tk.StringVar(value="")).get(),
                "extendedbe_enabled": getattr(self, "extendedbe_enabled_var", _tk.BooleanVar(value=False)).get()
            }
            # Ensure directory exists
            cache_dir = _os.path.dirname(settings_path)
            _os.makedirs(cache_dir, exist_ok=True)
            
            with open(settings_path, 'w', encoding='utf-8') as f:
                _json.dump(settings, f, indent=2)
            _logging.debug(f"Settings saved to: {settings_path}")
        except Exception as e:
            log_error(f"Failed to save settings: {e}")
            _logging.debug(f"Settings path was: {settings_path}")
            import traceback
            _logging.debug(traceback.format_exc())

    def _sanitize_playlist_key(self, value):
        """Normalize playlist key and block path traversal values."""
        try:
            s = str(value or "__all__").strip()
            if not s:
                return "__all__"
            s = s.replace("\\", "/").strip("/")
            if not s or s == "__all__":
                return "__all__"
            parts = [p for p in s.split("/") if p and p != "."]
            if not parts or any(p == ".." for p in parts):
                return "__all__"
            return "/".join(parts)
        except Exception:
            return "__all__"

    def _iter_supported_audio_files(self, base_dir):
        """Yield supported audio files recursively from base_dir."""
        supported = ('.ogg', '.mp3', '.wav')
        for root, _dirs, files in _os.walk(base_dir):
            for name in files:
                if not name or name.startswith('.'):
                    continue
                if _os.path.splitext(name)[1].lower() in supported:
                    path = _os.path.join(root, name)
                    if _os.path.isfile(path):
                        yield path

    def _get_available_music_playlists(self):
        """Return sorted playlist keys from subfolders under music roots."""
        playlists = set()
        for music_dir in _MUSIC_DIRS:
            if not music_dir or not _os.path.isdir(music_dir):
                continue
            try:
                for name in _os.listdir(music_dir):
                    if not name or name.startswith('.'):
                        continue
                    folder = _os.path.join(music_dir, name)
                    if _os.path.isdir(folder):
                        playlists.add(name.replace("\\", "/").strip("/"))
            except OSError:
                continue
        return sorted(playlists, key=lambda x: x.lower())

    def _get_music_file_list(self):
        """Return supported music files from selected playlist or all music."""
        paths = []
        selected_playlist = self._sanitize_playlist_key(
            getattr(self, "music_playlist_var", _tk.StringVar(value="__all__")).get()
        )
        for music_dir in _MUSIC_DIRS:
            if not music_dir or not _os.path.isdir(music_dir):
                continue
            try:
                if selected_playlist == "__all__":
                    for path in self._iter_supported_audio_files(music_dir):
                        if path not in paths:
                            paths.append(path)
                else:
                    playlist_dir = _os.path.join(music_dir, selected_playlist)
                    if _os.path.isdir(playlist_dir):
                        for path in self._iter_supported_audio_files(playlist_dir):
                            if path not in paths:
                                paths.append(path)
            except OSError as e:
                _logging.debug("Background music: could not list %s: %s", music_dir, e)
        if not paths:
            _logging.error(
                "Background music: no playable files for playlist '%s' (checked: %s)",
                selected_playlist,
                _MUSIC_DIRS,
            )
        return paths

    def _rebuild_music_order(self, keep_current=True):
        """Build playback order based on current files and shuffle setting."""
        paths = self._get_music_file_list()
        if not paths:
            self._music_order = []
            self._music_index = -1
            return []
        order = list(paths)
        if getattr(self, "music_shuffle_var", None) and self.music_shuffle_var.get():
            _random.shuffle(order)
        else:
            order.sort(key=lambda p: self._format_track_display_name(p).lower())
        # Prefer a canonical "background.*" track as first song when starting fresh.
        if order and int(getattr(self, "_music_index", -1)) < 0:
            preferred_idx = -1
            for i, p in enumerate(order):
                n = _os.path.splitext(_os.path.basename(p))[0].strip().lower()
                if n == "background":
                    preferred_idx = i
                    break
            if preferred_idx < 0:
                for i, p in enumerate(order):
                    n = _os.path.splitext(_os.path.basename(p))[0].strip().lower()
                    if n.startswith("background"):
                        preferred_idx = i
                        break
            if preferred_idx > 0:
                preferred = order.pop(preferred_idx)
                order.insert(0, preferred)
        current_path = getattr(self, "_current_track_path", None) if keep_current else None
        self._music_order = order
        if current_path and current_path in order:
            self._music_index = order.index(current_path)
        else:
            self._music_index = -1
        return order

    def _play_track_at_index(self, index, show_popup=True, popup_force=False):
        """Play the track at index in current music order. Returns True on success."""
        if not _PYGAME_MIXER_AVAILABLE or _pygame is None:
            return False
        order = list(getattr(self, "_music_order", []) or [])
        if not order:
            return False
        total = len(order)
        start = index % total
        last_err = None
        for offset in range(total):
            idx = (start + offset) % total
            path = order[idx]
            try:
                _pygame.mixer.music.load(path)
                _pygame.mixer.music.set_volume(self._get_music_volume())
                _pygame.mixer.music.play(loops=0)
                self._music_index = idx
                self._current_track_path = path
                self._current_track_name = self._format_track_display_name(path)
                # Re-apply volume shortly after play for pygame/Windows edge cases.
                def _reapply_vol():
                    try:
                        if _pygame and _pygame.mixer.get_init():
                            _pygame.mixer.music.set_volume(self._get_music_volume())
                    except Exception:
                        pass
                self._root.after(200, _reapply_vol)
                self._root.after(600, _reapply_vol)
                if show_popup:
                    self._show_now_playing(self._current_track_name, force=popup_force)
                # Update Discord presence with new song
                self._update_discord_presence()
                return True
            except Exception as e:
                last_err = e
                continue
        _logging.error("Background music: failed to play any track in current order. Last error: %s", last_err)
        return False

    def _play_next_track(self, show_popup=True, popup_force=False):
        """Play next track based on current order and shuffle setting."""
        try:
            if not getattr(self, "background_music_var", None) or not self.background_music_var.get():
                return False
            if not _PYGAME_MIXER_AVAILABLE or _pygame is None:
                return False
            current_path = getattr(self, "_current_track_path", None)
            current_files = self._get_music_file_list()
            if not current_files:
                return False
            order = list(getattr(self, "_music_order", []) or [])
            if (not order) or (set(order) != set(current_files)):
                order = self._rebuild_music_order(keep_current=True)
            if not order:
                return False
            idx = int(getattr(self, "_music_index", -1))
            if idx < 0 and current_path in order:
                idx = order.index(current_path)
                self._music_index = idx
            next_idx = idx + 1
            if next_idx >= len(order):
                if getattr(self, "music_shuffle_var", None) and self.music_shuffle_var.get():
                    last_path = current_path
                    _random.shuffle(order)
                    if last_path and len(order) > 1 and order[0] == last_path:
                        order.append(order.pop(0))
                    self._music_order = order
                next_idx = 0
            return self._play_track_at_index(next_idx, show_popup=show_popup, popup_force=popup_force)
        except Exception as e:
            _logging.error("Background music _play_next_track: %s", e)
            return False

    def _play_previous_track(self, show_popup=True, popup_force=False):
        """Play previous track based on current order."""
        try:
            if not getattr(self, "background_music_var", None) or not self.background_music_var.get():
                return False
            if not _PYGAME_MIXER_AVAILABLE or _pygame is None:
                return False
            order = list(getattr(self, "_music_order", []) or [])
            if not order:
                order = self._rebuild_music_order(keep_current=True)
            if not order:
                return False
            idx = int(getattr(self, "_music_index", -1))
            current_path = getattr(self, "_current_track_path", None)
            if idx < 0 and current_path in order:
                idx = order.index(current_path)
                self._music_index = idx
            prev_idx = (idx - 1) if idx > 0 else (len(order) - 1)
            return self._play_track_at_index(prev_idx, show_popup=show_popup, popup_force=popup_force)
        except Exception as e:
            _logging.error("Background music _play_previous_track: %s", e)
            return False

    def _start_music_end_watcher(self):
        """Ensure a single watcher advances track after current one ends."""
        if getattr(self, "_music_end_after_id", None) is not None:
            return
        def _poll():
            self._music_end_after_id = None
            try:
                if not getattr(self, "_root", None) or not self._root.winfo_exists():
                    return
                if not getattr(self, "background_music_var", None) or not self.background_music_var.get():
                    return
                busy = False
                try:
                    busy = bool(_PYGAME_MIXER_AVAILABLE and _pygame and _pygame.mixer.get_init() and _pygame.mixer.music.get_busy())
                except Exception:
                    busy = False
                if not busy:
                    self._play_next_track(show_popup=True, popup_force=True)
            except Exception:
                pass
            finally:
                if getattr(self, "_root", None) and self._root.winfo_exists() and getattr(self, "background_music_var", None) and self.background_music_var.get():
                    self._music_end_after_id = self._root.after(1200, _poll)
        self._music_end_after_id = self._root.after(1200, _poll)

    def _stop_music_end_watcher(self):
        """Stop track-end watcher timer."""
        if getattr(self, "_music_end_after_id", None) is not None:
            try:
                self._root.after_cancel(self._music_end_after_id)
            except Exception:
                pass
            self._music_end_after_id = None

    def _on_music_shuffle_setting_changed(self):
        """Rebuild order while keeping current track when shuffle mode changes."""
        try:
            self._rebuild_music_order(keep_current=True)
        except Exception:
            pass

    def _on_music_playlist_setting_changed(self):
        """Apply selected playlist and restart from that list when needed."""
        try:
            selected = self._sanitize_playlist_key(
                getattr(self, "music_playlist_var", _tk.StringVar(value="__all__")).get()
            )
            if getattr(self, "music_playlist_var", None) and self.music_playlist_var.get() != selected:
                self.music_playlist_var.set(selected)
                return
            self._rebuild_music_order(keep_current=False)
            if getattr(self, "_root", None) and self._root.winfo_exists():
                refresh_fn = getattr(self, "_settings_refresh_now_playing", None)
                if callable(refresh_fn):
                    try:
                        self._root.after(0, refresh_fn)
                    except Exception:
                        pass
            if not getattr(self, "background_music_var", None) or not self.background_music_var.get():
                return
            if not _PYGAME_MIXER_AVAILABLE or _pygame is None:
                return
            if not getattr(self, "_music_order", None):
                try:
                    _pygame.mixer.music.stop()
                except Exception:
                    pass
                self._current_track_name = None
                self._current_track_path = None
                # Update Discord presence to clear song
                self._update_discord_presence()
                return
            self._play_track_at_index(0, show_popup=True, popup_force=True)
            self._start_music_end_watcher()
        except Exception:
            pass

    def _format_track_display_name(self, value):
        """Create a clean human-readable track title from filename/path."""
        try:
            if value is None:
                return "Unknown"
            raw = str(value).strip()
            if not raw:
                return "Unknown"
            # Accept either full path or filename/title
            name = _os.path.splitext(_os.path.basename(raw))[0]
            # Remove common numeric prefixes like "01 - " / "001_" / "12. "
            name = _re.sub(r'^\s*\d+\s*[-_.\)\]]+\s*', '', name)
            # Normalize separators and whitespace
            name = name.replace('_', ' ').strip()
            name = _re.sub(r'\s{2,}', ' ', name)
            return name or "Unknown"
        except Exception:
            return "Unknown"

    def _ellipsize_text(self, text, tk_font, max_width):
        """Trim text with ellipsis so it fits within max_width pixels."""
        try:
            s = str(text or "")
            if not s:
                return ""
            if tk_font.measure(s) <= max_width:
                return s
            ell = "..."
            if tk_font.measure(ell) > max_width:
                return ""
            lo, hi = 0, len(s)
            while lo < hi:
                mid = (lo + hi + 1) // 2
                cand = s[:mid].rstrip() + ell
                if tk_font.measure(cand) <= max_width:
                    lo = mid
                else:
                    hi = mid - 1
            return s[:lo].rstrip() + ell
        except Exception:
            return str(text or "")

    def _play_next_shuffled_track(self):
        """Play one random track from the music folder; when it ends, schedule the next (shuffle)."""
        self._play_next_track(show_popup=True, popup_force=True)

    def _start_background_music(self):
        """Play non-copyright background music from music/ folder (shuffled). Turn on/off in Settings."""
        try:
            if not getattr(self, "background_music_var", None) or not self.background_music_var.get():
                return
            if not _PYGAME_MIXER_AVAILABLE or _pygame is None:
                return
            # Initialize full pygame first (helps mixer on some Windows setups)
            try:
                _pygame.init()
            except Exception:
                pass
            if not _pygame.mixer.get_init():
                for kwargs in [
                    {"frequency": 44100, "size": -16, "channels": 2, "buffer": 512},
                    {"frequency": 22050, "size": -16, "channels": 2, "buffer": 1024},
                    {},
                ]:
                    try:
                        if kwargs:
                            _pygame.mixer.init(**kwargs)
                        else:
                            _pygame.mixer.init()
                        break
                    except Exception as e:
                        _logging.error("pygame.mixer.init failed: %s", e)
                        if not kwargs:
                            return
            # If music is already playing, don't restart/reorder; just keep watcher alive.
            try:
                if _pygame.mixer.get_init() and _pygame.mixer.music.get_busy() and getattr(self, "_current_track_path", None):
                    self._start_music_end_watcher()
                    return
            except Exception:
                pass
            try:
                _pygame.mixer.music.stop()
            except Exception:
                pass
            self._rebuild_music_order(keep_current=False)
            self._play_next_track(show_popup=True, popup_force=True)
            self._start_music_end_watcher()
        except Exception as e:
            _logging.error("_start_background_music: %s", e)

    def _show_now_playing(self, track_name, force=False):
        """Show an in-app 'Now Playing' popup with fade in/out animation."""
        try:
            if not getattr(self, "_root", None) or not self._root.winfo_exists():
                return
            track_name = self._format_track_display_name(track_name)
            _now = _time.monotonic()
            _last_popup_at = float(getattr(self, "_last_now_playing_at", 0.0) or 0.0)
            _last_popup_track = getattr(self, "_last_now_playing_track", None)
            # Always show popup on genuine song changes. Only suppress rapid duplicate spam.
            if not force and _last_popup_track == track_name and (_now - _last_popup_at) < 0.7:
                return
            self._last_now_playing_at = _now
            self._last_now_playing_track = track_name
            self._now_playing_anim_token = int(getattr(self, "_now_playing_anim_token", 0)) + 1
            _token = self._now_playing_anim_token
            # Cancel any existing now-playing popup
            if getattr(self, "_now_playing_popup", None) and self._now_playing_popup.winfo_exists():
                try:
                    self._now_playing_popup.destroy()
                except Exception:
                    pass
            if getattr(self, "_now_playing_after_id", None) is not None:
                try:
                    self._root.after_cancel(self._now_playing_after_id)
                except Exception:
                    pass
                self._now_playing_after_id = None
            if getattr(self, "_now_playing_marquee_after_id", None) is not None:
                try:
                    self._root.after_cancel(self._now_playing_marquee_after_id)
                except Exception:
                    pass
                self._now_playing_marquee_after_id = None
            popup_w, popup_h = 300, 72
            pw = _tk.Frame(self._root, bg="#1a1a1a", highlightthickness=1, highlightbackground="#9333ea", bd=0)
            inner = _tk.Frame(pw, bg="#1a1a1a", padx=16, pady=12)
            inner.pack(fill="both", expand=True)
            header_lbl = _tk.Label(inner, text="Now Playing", bg="#1a1a1a", fg="#9333ea", font=("Segoe UI", 10, "bold"))
            header_lbl.pack(anchor="w")
            _text_font = _font.Font(family="Segoe UI", size=12)
            _text_label_w = popup_w - 32
            track_canvas = _tk.Canvas(inner, width=_text_label_w, height=22, bg="#1a1a1a", highlightthickness=0)
            track_canvas.pack(anchor="w", fill="x")
            _popup_np_text = track_name or "Unknown"
            _popup_np_width = _text_font.measure(_popup_np_text)
            _track_text_item = None
            if _popup_np_width <= _text_label_w:
                _track_text_item = track_canvas.create_text(_text_label_w // 2, 11, text=_popup_np_text, fill="#FFFFFF", font=("Segoe UI", 12), anchor="center")
            else:
                _gap = "     "
                _loop_text = _popup_np_text + _gap + _popup_np_text
                _reset_at = _text_font.measure(_popup_np_text + _gap)
                _tid = track_canvas.create_text(0, 11, text=_loop_text, fill="#FFFFFF", font=("Segoe UI", 12), anchor="w")
                _track_text_item = _tid
                _x = [0.0]
                _SCROLL_MS = 16  # ~60 FPS
                _SCROLL_PX = 0.8
                def _popup_marquee_step():
                    if _token != getattr(self, "_now_playing_anim_token", -1):
                        return
                    if not pw.winfo_exists() or not track_canvas.winfo_exists():
                        return
                    try:
                        track_canvas.coords(_tid, _x[0], 11)
                        _x[0] -= _SCROLL_PX
                        if _x[0] <= -_reset_at:
                            _x[0] = 0.0
                        self._now_playing_marquee_after_id = self._root.after(_SCROLL_MS, _popup_marquee_step)
                    except Exception:
                        pass
                self._now_playing_marquee_after_id = self._root.after(350, _popup_marquee_step)
            self._now_playing_popup = pw
            pw.lift()

            try:
                self._root.update_idletasks()
            except Exception:
                return
            rw = self._root.winfo_width()
            x = max(0, rw // 2 - popup_w // 2)
            y_pos = 16

            def _place():
                if _token != getattr(self, "_now_playing_anim_token", -1):
                    return
                if pw.winfo_exists():
                    pw.place(x=x, y=int(y_pos), width=popup_w, height=popup_h)

            def _hex_to_rgb(value):
                v = str(value or "").lstrip("#")
                if len(v) != 6:
                    return (255, 255, 255)
                return (int(v[0:2], 16), int(v[2:4], 16), int(v[4:6], 16))

            def _rgb_to_hex(rgb):
                r, g, b = [max(0, min(255, int(c))) for c in rgb]
                return f"#{r:02x}{g:02x}{b:02x}"

            def _blend(c0, c1, t):
                t = max(0.0, min(1.0, float(t)))
                a = _hex_to_rgb(c0)
                b = _hex_to_rgb(c1)
                return _rgb_to_hex((
                    a[0] + (b[0] - a[0]) * t,
                    a[1] + (b[1] - a[1]) * t,
                    a[2] + (b[2] - a[2]) * t,
                ))

            def _apply_fade(alpha):
                if _token != getattr(self, "_now_playing_anim_token", -1):
                    return
                if not pw.winfo_exists():
                    return
                # Fake opacity by blending toward root bg.
                try:
                    base_bg = "#1a1a1a"
                    root_bg = "#000000"
                    accent = "#9333ea"
                    text_white = "#ffffff"
                    bg_now = _blend(root_bg, base_bg, alpha)
                    accent_now = _blend(root_bg, accent, alpha)
                    text_now = _blend(root_bg, text_white, alpha)
                    pw.configure(bg=bg_now, highlightbackground=accent_now)
                    inner.configure(bg=bg_now)
                    header_lbl.configure(bg=bg_now, fg=accent_now)
                    track_canvas.configure(bg=bg_now)
                    if _track_text_item is not None:
                        track_canvas.itemconfig(_track_text_item, fill=text_now)
                except Exception:
                    pass

            def _destroy_popup():
                if _token != getattr(self, "_now_playing_anim_token", -1):
                    return
                try:
                    if pw.winfo_exists():
                        pw.place_forget()
                        pw.destroy()
                except Exception:
                    pass
                if getattr(self, "_now_playing_popup", None) is pw:
                    self._now_playing_popup = None
                self._now_playing_after_id = None
                if getattr(self, "_now_playing_marquee_after_id", None) is not None:
                    try:
                        self._root.after_cancel(self._now_playing_marquee_after_id)
                    except Exception:
                        pass
                    self._now_playing_marquee_after_id = None

            def _fade_in(step=0):
                if _token != getattr(self, "_now_playing_anim_token", -1):
                    return
                if not pw.winfo_exists():
                    return
                steps_total = 14
                if step <= steps_total:
                    t = step / steps_total
                    eased = 1 - (1 - t) ** 2
                    _apply_fade(eased)
                    next_step = step + 1
                    self._now_playing_after_id = self._root.after(16, lambda ns=next_step: _fade_in(ns))
                else:
                    self._now_playing_after_id = self._root.after(3000, _fade_out)

            def _fade_out(step=0):
                if _token != getattr(self, "_now_playing_anim_token", -1):
                    return
                if not pw.winfo_exists():
                    return
                steps_total = 16
                if step <= steps_total:
                    t = step / steps_total
                    # Ease-out fade for a soft disappear.
                    alpha = 1 - (t * t)
                    _apply_fade(alpha)
                    next_step = step + 1
                    self._now_playing_after_id = self._root.after(16, lambda ns=next_step: _fade_out(ns))
                else:
                    _destroy_popup()

            _place()
            _apply_fade(0.0)
            self._now_playing_after_id = self._root.after(25, lambda: _fade_in(0))
        except Exception:
            pass

    def _stop_background_music(self):
        """Stop background music."""
        setattr(self, "_current_track_name", None)
        setattr(self, "_current_track_path", None)
        setattr(self, "_music_index", -1)
        self._stop_music_end_watcher()
        # Update Discord presence to clear song
        self._update_discord_presence()
        if not _PYGAME_MIXER_AVAILABLE or _pygame is None:
            return
        try:
            _pygame.mixer.music.stop()
        except Exception:
            pass

    def _get_music_volume(self):
        """Return background music volume as float 0.0–1.0 from settings. If slider is 0, use 0.05 so we don't get silent playback by mistake."""
        v = getattr(self, "background_music_volume_var", None)
        if v is None:
            return 0.7
        raw = min(1.0, max(0.0, v.get() / 100.0))
        return 0.05 if raw == 0 else raw

    def _apply_background_music_volume(self, *args):
        """Apply current music volume to pygame mixer if playing."""
        try:
            if not _PYGAME_MIXER_AVAILABLE or _pygame is None:
                return
            if _pygame.mixer.get_init():
                _pygame.mixer.music.set_volume(self._get_music_volume())
        except Exception:
            pass

    def _apply_background_music_setting(self, *args):
        """Called when background music setting changes: start or stop music."""
        try:
            if getattr(self, "background_music_var", None) and self.background_music_var.get():
                self._start_background_music()
            else:
                self._stop_background_music()
        except Exception:
            pass
    
    def _fetch_github_file(self, file_path):
        """Fetch a file from GitHub using the API with token. Returns None if network/DNS fails (offline)."""
        _headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        api_url = f"https://api.github.com/repos/FrostyHostMC/AutoBE/contents/{file_path}"
        try:
            response = _requests.get(api_url, headers=_headers, timeout=10)
            response.raise_for_status()
            file_data = response.json()
            content = base64.b64decode(file_data['content']).decode('utf-8')
            return content
        except (_requests.exceptions.ConnectionError, _requests.exceptions.Timeout, _requests.exceptions.HTTPError, OSError) as e:
            _logging.debug("GitHub fetch failed (network/HTTP error): %s", e)
            return None
        except Exception:
            raise

    def _version_tuple(self, v):
        """Convert version string to tuple of ints for comparison."""
        s = str(v).strip().lstrip('vV').splitlines()[0].strip()
        try:
            return tuple(int(x) for x in s.split('.') if x.isdigit())
        except (ValueError, AttributeError):
            return (0,)

    def _get_windows_exe_version(self, exe_path):
        """Read Windows EXE file version (e.g. 7.0.2.0) via PowerShell."""
        if platform.system() != "Windows":
            return None
        try:
            safe = str(exe_path or "").replace("'", "''")
            cmd = f"(Get-Item -LiteralPath '{safe}').VersionInfo.FileVersion"
            flags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
            proc = subprocess.run(
                ["powershell", "-NoProfile", "-Command", cmd],
                capture_output=True,
                text=True,
                timeout=12,
                creationflags=flags,
            )
            out = ((proc.stdout or "") + "\n" + (proc.stderr or "")).strip()
            m = _re.search(r"\d+(?:\.\d+){1,3}", out)
            return m.group(0) if m else None
        except Exception:
            return None

    def _check_for_updates(self):
        """User clicked Check for updates: close dropdown and run check (show 'Up to date' if no update)."""
        self._close_settings_dropdown()
        self._run_update_check(silent_if_up_to_date=False)

    def _run_update_check(self, silent_if_up_to_date=False):
        """Check version.txt line 2 and GitHub Releases. If newer version exists, show Update available. If silent_if_up_to_date, don't show anything when already up to date (used for auto-check on startup)."""
        with self._update_check_lock:
            if getattr(self, '_update_check_in_progress', False):
                return
            self._update_check_in_progress = True

        def do_check():
            try:
                version_text = self._fetch_github_file("version.txt")
                if not version_text:
                    return
                lines = version_text.strip().splitlines()
                latest_str = (lines[1].strip() if len(lines) > 1 else '').lstrip('vV')
                if not latest_str or self._version_tuple(latest_str) <= self._version_tuple(APP_VERSION):
                    if not silent_if_up_to_date:
                        self._root.after(0, lambda: self._show_themed_info_dialog(_("update.title"), _("update.up_to_date") + "\n" + _f("update.current_version", version=APP_VERSION)))
                    return
                headers = {"Accept": "application/vnd.github.v3+json"}
                if GITHUB_TOKEN:
                    headers["Authorization"] = f"token {GITHUB_TOKEN}"
                # Prefer exact tag from version.txt so we never depend on GitHub "latest" ordering.
                tag_candidates = [f"v{latest_str}", latest_str]
                data = None
                last_http = None
                for _tag in tag_candidates:
                    try:
                        url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/tags/{_tag}"
                        r = _requests.get(url, headers=headers, timeout=10)
                        last_http = r.status_code
                        if r.status_code == 200:
                            data = r.json()
                            break
                    except Exception:
                        pass
                if data is None:
                    # Fallback to /latest only if exact-tag lookup failed.
                    try:
                        url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
                        r = _requests.get(url, headers=headers, timeout=10)
                        last_http = r.status_code
                        if r.status_code == 200:
                            data = r.json()
                    except Exception as release_err:
                        log_error(release_err)
                if data is None:
                    if not silent_if_up_to_date:
                        def show_no_release():
                            if hasattr(self, '_settings_dropdown') and self._settings_dropdown.winfo_exists():
                                self._root.after(1000, show_no_release)
                                return
                            self._show_update_available_no_release(latest_str)
                        self._root.after(0, show_no_release)
                    return
                # Ensure release metadata matches version.txt before offering update.
                release_tag = str((data or {}).get("tag_name") or "").strip().lstrip('vV')
                if not release_tag or self._version_tuple(release_tag) != self._version_tuple(latest_str):
                    if not silent_if_up_to_date:
                        def show_no_release():
                            if hasattr(self, '_settings_dropdown') and self._settings_dropdown.winfo_exists():
                                self._root.after(1000, show_no_release)
                                return
                            self._show_update_available_no_release(latest_str)
                        self._root.after(0, show_no_release)
                    return
                if not silent_if_up_to_date:
                    def show():
                        if hasattr(self, '_settings_dropdown') and self._settings_dropdown.winfo_exists():
                            self._root.after(1000, show)
                            return
                        self._show_update_available(latest_str, data)
                    self._root.after(0, show)
            except Exception as e:
                log_error(e)
                if not silent_if_up_to_date:
                    self._root.after(0, lambda: self._show_themed_info_dialog(_("update.title"), _("update.check_failed")))
            finally:
                self._root.after(0, lambda: setattr(self, '_update_check_in_progress', False))

        threading.Thread(target=do_check, daemon=True).start()

    def _auto_check_for_updates(self):
        """Run once after startup: detect new release and show Update available only if one exists. No popup if up to date."""
        self._run_update_check(silent_if_up_to_date=True)

    def _periodic_update_check(self):
        """Background check every UPDATE_CHECK_INTERVAL_MS. Keeps app aware of new releases without opening a dialog when up to date."""
        if getattr(self, '_root', None) and self._root.winfo_exists():
            self._run_update_check(silent_if_up_to_date=True)
            self._root.after(UPDATE_CHECK_INTERVAL_MS, self._periodic_update_check)

    def _show_update_available_no_release(self, new_version):
        """No release found that matches the latest version in version.txt — themed message, OK only. When a release is ready they'll see Update now / Later."""
        if getattr(self, '_update_no_release_dialog_shown', False):
            return
        self._update_no_release_dialog_shown = True
        def on_destroy():
            self._update_no_release_dialog_shown = False
        self._show_themed_info_dialog(_("update.no_release_title"), _f("update.no_release_msg", version=new_version), on_destroy=on_destroy)

    def _show_update_available(self, new_version, release_data):
        """Show themed Update available dialog; on Update now run auto-install."""
        self._show_themed_update_prompt(new_version, release_data)

    def _show_themed_info_dialog(self, title, message, on_destroy=None, topmost=False):
        """Show themed one-button dialog (e.g. Up to date, or Update not ready). Fixed size, no resize. Optional on_destroy() when dialog is closed."""
        dlg = _tk.Toplevel(self._root)
        self._apply_window_icon(dlg)
        dlg.title(title)
        dlg.configure(bg='#000000')
        w, h = 420, 280
        dlg.geometry(f"{w}x{h}")
        dlg.minsize(w, h)
        dlg.maxsize(w, h)
        dlg.resizable(False, False)
        dlg.overrideredirect(True)
        dlg.transient(self._root)
        dlg.grab_set()
        if topmost:
            try:
                dlg.attributes("-topmost", True)
                dlg.after(1800, lambda: dlg.winfo_exists() and dlg.attributes("-topmost", False))
            except Exception:
                pass
        dlg.update_idletasks()
        rx, ry = self._root.winfo_x(), self._root.winfo_y()
        rw, rh = self._root.winfo_width(), self._root.winfo_height()
        x = rx + max(0, (rw - w) // 2)
        y = ry + max(0, (rh - h) // 2)
        dlg.geometry(f"+{x}+{y}")
        dlg.grid_columnconfigure(0, weight=1)
        dlg.grid_rowconfigure(0, weight=0)
        dlg.grid_rowconfigure(1, weight=1)

        _drag = {"x": 0, "y": 0}
        def _drag_start(event):
            _drag["x"] = event.x_root - dlg.winfo_x()
            _drag["y"] = event.y_root - dlg.winfo_y()
        def _drag_move(event):
            dlg.geometry(f"+{event.x_root - _drag['x']}+{event.y_root - _drag['y']}")

        if on_destroy:
            def _on_destroy(event):
                if event.widget == dlg:
                    try:
                        on_destroy()
                    except Exception:
                        pass
            dlg.bind('<Destroy>', _on_destroy)

        titlebar = _tk.Frame(dlg, bg="#000000", height=34, highlightthickness=1, highlightbackground="#1f1f1f")
        titlebar.grid(row=0, column=0, sticky="ew")
        titlebar.grid_columnconfigure(1, weight=1)
        titlebar.grid_propagate(False)
        dlg._titlebar_icon_img = _get_titlebar_icon_image(14)
        if dlg._titlebar_icon_img is not None:
            title_icon = _tk.Label(titlebar, image=dlg._titlebar_icon_img, bg="#000000")
        else:
            title_icon = _tk.Label(titlebar, text="◈", bg="#000000", fg="#9333ea", font=("Segoe UI", 10, "bold"))
        title_icon.grid(row=0, column=0, padx=(10, 6), sticky="w")
        title_lbl = _tk.Label(titlebar, text=title, bg="#000000", fg="#E5E7EB", font=("Segoe UI", 10, "bold"))
        title_lbl.grid(row=0, column=1, padx=(0, 6), sticky="w")
        _tk.Button(
            titlebar, text="✕", command=dlg.destroy, bg="#000000", fg="#E5E7EB",
            font=("Segoe UI", 10, "bold"), relief="flat", bd=0, padx=12, pady=3,
            activebackground="#c42b1c", activeforeground="#FFFFFF", cursor="hand2"
        ).grid(row=0, column=2, sticky="e")
        for _w in (titlebar, title_icon, title_lbl):
            _w.bind("<ButtonPress-1>", _drag_start, add="+")
            _w.bind("<B1-Motion>", _drag_move, add="+")

        main = _tk.Frame(dlg, bg='#0f1419', padx=24, pady=24)
        main.grid(row=1, column=0, sticky="nsew")
        _tk.Frame(main, bg='#9333ea', height=3).pack(fill='x', pady=(0, 16))
        _tk.Label(main, text=title, bg='#0f1419', fg='#FFFFFF', font=('Segoe UI', 16, 'bold')).pack(anchor='w')
        _tk.Label(main, text=message, bg='#0f1419', fg='#e5e7eb', font=('Segoe UI', 10), justify='left', wraplength=360).pack(anchor='w', pady=(12, 24))
        _tk.Button(main, text=_("common.ok"), command=dlg.destroy, bg='#9333ea', fg='#FFFFFF', font=('Segoe UI', 11, 'bold'), relief='flat', cursor='hand2', activebackground='#a855f7', padx=28, pady=8).pack(anchor='s', pady=(16, 0))

    def _show_themed_update_prompt(self, new_version, release_data):
        """Themed dialog: Update available — Update now / Later. Fixed size, no resize. Click only."""
        dlg = _tk.Toplevel(self._root)
        self._apply_window_icon(dlg)
        dlg.title(_("update.available"))
        dlg.configure(bg='#0f1419')
        w, h = 460, 300
        dlg.geometry(f"{w}x{h}")
        dlg.minsize(w, h)
        dlg.maxsize(w, h)
        dlg.resizable(False, False)
        dlg.transient(self._root)
        dlg.grab_set()
        dlg.update_idletasks()
        rx, ry = self._root.winfo_x(), self._root.winfo_y()
        rw, rh = self._root.winfo_width(), self._root.winfo_height()
        x = rx + max(0, (rw - w) // 2)
        y = ry + max(0, (rh - h) // 2)
        dlg.geometry(f"+{x}+{y}")
        main = _tk.Frame(dlg, bg='#0f1419', padx=24, pady=24)
        main.pack(fill='both', expand=True)
        _tk.Frame(main, bg='#9333ea', height=3).pack(fill='x', pady=(0, 16))
        _tk.Label(main, text=_("update.available"), bg='#0f1419', fg='#FFFFFF', font=('Segoe UI', 16, 'bold')).pack(anchor='w')
        _tk.Label(main, text=_f("update.your_version", current=APP_VERSION, new=new_version), bg='#0f1419', fg='#a78bfa', font=('Segoe UI', 11)).pack(anchor='w', pady=(8, 12))
        _tk.Label(main, text=_("update.will_download"), bg='#0f1419', fg='#e5e7eb', font=('Segoe UI', 10), justify='left').pack(anchor='w', pady=(0, 20))
        btn_frame = _tk.Frame(main, bg='#0f1419')
        btn_frame.pack(fill='x')
        def on_update():
            dlg.destroy()
            self._do_auto_update(release_data, expected_version=new_version)
        def on_later():
            dlg.destroy()
        _tk.Button(btn_frame, text=_("update.now"), command=on_update, bg='#9333ea', fg='#FFFFFF', font=('Segoe UI', 11, 'bold'), relief='flat', cursor='hand2', activebackground='#a855f7', padx=24, pady=10).pack(side='left', padx=(0, 12))
        _tk.Button(btn_frame, text=_("update.later"), command=on_later, bg='#2a2a2a', fg='#e5e7eb', font=('Segoe UI', 11), relief='flat', cursor='hand2', activebackground='#3a3a3a', padx=24, pady=10).pack(side='left')

    def _show_update_overlay_ui(self, status_text):
        """Show full-screen update overlay (themed like verification): title + status + spinner."""
        for w in self._update_overlay.winfo_children():
            w.destroy()
        self._update_overlay.grid_columnconfigure(0, weight=1)
        self._update_overlay.grid_rowconfigure(0, weight=1)
        center = _tk.Frame(self._update_overlay, bg='#000000')
        center.place(relx=0.5, rely=0.5, anchor='center')
        _tk.Label(center, text=_("update.updating"), bg='#000000', fg='#FFFFFF', font=('Segoe UI', 20, 'bold')).pack(pady=(0, 40))
        spinner_frame = _tk.Frame(center, bg='#000000')
        spinner_frame.pack(pady=20)
        dot_colors = ['#FF0000', '#00FF00', '#0000FF', '#FFFF00', '#FF00FF', '#00FFFF']
        self._update_dots = []
        for i in range(6):
            dot = _tk.Label(spinner_frame, text="●", bg='#000000', fg=dot_colors[i], font=('Segoe UI', 24, 'bold'))
            dot.pack(side=_tk.LEFT, padx=5)
            self._update_dots.append(dot)
        self._update_status_label = _tk.Label(center, text=status_text, bg='#000000', fg='#9333ea', font=('Segoe UI', 12))
        self._update_status_label.pack(pady=30)
        self._update_overlay.grid()
        self._update_overlay.lift()
        self._root.update_idletasks()
        self._update_anim_step = 0
        self._update_animate()

    def _update_animate(self):
        """Animate spinner on update overlay."""
        if not hasattr(self, '_update_status_label') or not self._update_status_label.winfo_exists():
            return
        step = getattr(self, '_update_anim_step', 0)
        for i, dot in enumerate(getattr(self, '_update_dots', [])):
            if not dot.winfo_exists():
                return
            phase = (step + i * 60) % 360
            r = int(127.5 * (1 + math.sin(math.radians(phase))))
            g = int(127.5 * (1 + math.sin(math.radians(phase + 120))))
            b = int(127.5 * (1 + math.sin(math.radians(phase + 240))))
            dot.config(fg=f"#{r:02x}{g:02x}{b:02x}")
        self._update_anim_step = step + 5
        self._root.after(50, self._update_animate)

    def _update_overlay_set_status(self, text):
        if hasattr(self, '_update_status_label') and self._update_status_label.winfo_exists():
            self._update_status_label.config(text=text)

    def _do_auto_update(self, release_data, expected_version=None):
        """Run updater (Windows prefers full installer upgrade; fallback to exe swap)."""
        def do_download():
            def fail_update(reason):
                self._root.after(
                    0,
                    lambda msg=reason: self._offer_installer_fallback_update(
                        release_data=release_data,
                        expected_version=expected_version,
                        fail_message=msg,
                    ),
                )
            try:
                self._root.after(0, lambda: self._show_update_overlay_ui(_("update.downloading")))
                assets = release_data.get('assets') or []
                current_exe = sys.executable
                current_name = _os.path.basename(current_exe).lower()
                # Guard: only proceed when release tag matches the version user was prompted for.
                release_tag = str((release_data or {}).get("tag_name") or "").strip().lstrip('vV')
                if expected_version and release_tag:
                    if self._version_tuple(release_tag) != self._version_tuple(expected_version):
                        fail_update(f"Update aborted: release tag ({release_tag}) does not match expected version ({expected_version}).")
                        return
                # Prefer full installer updates on Windows for reliability and complete file replacement.
                if platform.system() == "Windows":
                    installer_asset = self._pick_installer_asset(release_data, expected_version=expected_version)
                    if installer_asset:
                        self._installer_fallback_in_progress = True
                        self._root.after(0, lambda: self._update_overlay_set_status("Downloading full installer update..."))
                        self._download_and_run_installer_fallback(installer_asset)
                        return
                def _is_runtime_exe_asset(a):
                    name = (a.get('name') or '').strip().lower()
                    if not name.endswith('.exe'):
                        return False
                    bad_markers = ("setup", "installer", "updater", "signtool", "portable", "unins", "uninstall")
                    if any(m in name for m in bad_markers):
                        return False
                    # In-app updater only supports runtime app executables.
                    if name == current_name or name == "autobe.exe":
                        return True
                    if "autobe" in name:
                        return True
                    return False
                def _asset_score(a):
                    """Higher score = better candidate for in-app exe replacement."""
                    name = (a.get('name') or '').strip().lower()
                    if not _is_runtime_exe_asset(a):
                        return -1
                    score = 0
                    if name == current_name:
                        score += 1000
                    if "autobe" in name:
                        score += 200
                    # Prefer larger binaries (one-file builds are typically larger than helper exes).
                    try:
                        size = int(a.get('size') or 0)
                    except Exception:
                        size = 0
                    score += min(size // (1024 * 1024), 200)  # up to +200 for size
                    return score
                candidates = [a for a in assets if _is_runtime_exe_asset(a)]
                ranked = sorted(candidates, key=_asset_score, reverse=True)
                exe_asset = ranked[0] if ranked and _asset_score(ranked[0]) >= 0 else None
                if not exe_asset:
                    fail_update(_("update.not_ready_no_file"))
                    return
                # Private repos: MUST use asset API url with token. browser_download_url returns 404 with token.
                if GITHUB_TOKEN:
                    download_url = exe_asset.get('url')
                    if not download_url and exe_asset.get('id'):
                        download_url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/assets/{exe_asset['id']}"
                else:
                    download_url = exe_asset.get('browser_download_url')
                if not download_url:
                    fail_update(_("update.not_ready"))
                    return
                if not current_exe.lower().endswith('.exe'):
                    fail_update(_("update.manual_only"))
                    return
                td = _tempfile.gettempdir()
                new_exe = _os.path.join(td, "AutoBE_update.exe")
                headers = {"Accept": "application/octet-stream"}
                if GITHUB_TOKEN:
                    headers["Authorization"] = f"token {GITHUB_TOKEN}"
                _last_download_url = download_url
                r = _requests.get(download_url, headers=headers, timeout=60, stream=True, allow_redirects=True)
                r.raise_for_status()
                with open(new_exe, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                # Basic integrity checks to avoid replacing with a broken/partial file.
                downloaded_size = _os.path.getsize(new_exe) if _os.path.exists(new_exe) else 0
                expected_size = int(exe_asset.get('size') or 0)
                if downloaded_size <= 0:
                    fail_update("Update failed: downloaded file is empty.")
                    return
                if expected_size > 0 and downloaded_size != expected_size:
                    fail_update(f"Update failed: file size mismatch (expected {expected_size}, got {downloaded_size}).")
                    return
                if downloaded_size < 2 * 1024 * 1024:
                    fail_update("Update failed: downloaded .exe is unexpectedly small. Release asset may be incorrect.")
                    return
                # Hard guard: ensure downloaded EXE version matches the expected release version.
                if expected_version:
                    downloaded_ver = self._get_windows_exe_version(new_exe)
                    if not downloaded_ver:
                        fail_update(
                            "Update failed: could not verify downloaded EXE version metadata. "
                            "Rebuild and upload a versioned AutoBE.exe asset."
                        )
                        return
                    if self._version_tuple(downloaded_ver) != self._version_tuple(expected_version):
                        fail_update(
                            f"Update aborted: downloaded EXE version ({downloaded_ver}) does not match expected "
                            f"version ({expected_version})."
                        )
                        return
                # Hard guard: block Python 3.13 runtime updates to prevent known python313.dll startup failures.
                try:
                    with open(new_exe, "rb") as _bf:
                        _blob = _bf.read()
                    if b"python313.dll" in _blob.lower():
                        fail_update(
                            "Update blocked: release EXE contains Python 3.13 runtime (python313.dll), "
                            "which is known to fail on some user PCs. Publish a Python 3.12 build."
                        )
                        return
                except Exception:
                    pass
                self._root.after(0, lambda: self._update_overlay_set_status(_("update.installing")))
                self._root.after(500, lambda: self._run_updater_batch(new_exe, current_exe))
            except Exception as e:
                log_error(e)
                try:
                    used_api = "api.github.com" in str(_last_download_url)
                except NameError:
                    used_api = False
                hint = "\n\n(Using API. If 404: check token has repo scope; or rebuild this exe from current AutoBE.py.)" if used_api else "\n\n(Rebuild this exe from current AutoBE.py so private-repo update works.)"
                fail_update(f"Update failed: {str(e)}{hint}")

        threading.Thread(target=do_download, daemon=True).start()

    def _run_updater_batch(self, new_exe, current_exe):
        """Write and run the batch that replaces exe and restarts. Then exit."""
        try:
            td = _tempfile.gettempdir()
            batch = _os.path.join(td, "AutoBE_updater.bat")
            marker_file = _os.path.join(td, f"AutoBE_update_ok_{int(_time.time())}_{_random.randint(1000, 9999)}.marker")
            result_file = _os.path.join(td, f"AutoBE_update_result_{int(_time.time())}_{_random.randint(1000, 9999)}.txt")
            fallback_result_file = _get_update_result_fallback_path()
            with open(batch, 'w') as f:
                f.write('@echo off\n')
                f.write('setlocal EnableExtensions\n')
                f.write('set "SRC=' + new_exe.replace('"', '""') + '"\n')
                f.write('set "DST=' + current_exe.replace('"', '""') + '"\n')
                f.write('set "BAK=' + (current_exe + ".preupdate.bak").replace('"', '""') + '"\n')
                f.write('set "MARK=' + marker_file.replace('"', '""') + '"\n')
                f.write('set "RES=' + result_file.replace('"', '""') + '"\n')
                f.write('set "RESP=' + fallback_result_file.replace('"', '""') + '"\n')
                f.write('del "%MARK%" 2>nul\n')
                f.write('del "%RES%" 2>nul\n')
                f.write('del "%RESP%" 2>nul\n')
                f.write('copy /y "%DST%" "%BAK%" >nul\n')
                f.write('set "COPIED_OK=0"\n')
                f.write('for /L %%I in (1,1,8) do (\n')
                f.write('    timeout /t 1 /nobreak >nul\n')
                f.write('    copy /y "%SRC%" "%DST%" >nul\n')
                f.write('    if errorlevel 1 (\n')
                f.write('        rem copy failed this round, retry\n')
                f.write('    ) else (\n')
                f.write('        for %%S in ("%SRC%") do set "SRC_SIZE=%%~zS"\n')
                f.write('        for %%D in ("%DST%") do set "DST_SIZE=%%~zD"\n')
                f.write('        if "%SRC_SIZE%"=="%DST_SIZE%" (\n')
                f.write('            set "COPIED_OK=1"\n')
                f.write('            goto :copied\n')
                f.write('        )\n')
                f.write('    )\n')
                f.write(')\n')
                f.write(':copied\n')
                f.write('if "%COPIED_OK%"=="1" (\n')
                f.write('    > "%RES%" echo UPDATED_OK\n')
                f.write('    > "%RESP%" echo UPDATED_OK\n')
                f.write('    start "" "%DST%" --post-update-check "%MARK%" --post-update-result "%RES%"\n')
                f.write('    for /L %%J in (1,1,25) do (\n')
                f.write('        timeout /t 1 /nobreak >nul\n')
                f.write('        if exist "%MARK%" goto :healthy\n')
                f.write('    )\n')
                f.write('    goto :rollback\n')
                f.write(') else (\n')
                f.write('    rem Do not run from temp fallback; keep installed path authoritative.\n')
                f.write('    > "%RES%" echo UPDATED_COPY_FAILED\n')
                f.write('    > "%RESP%" echo UPDATED_COPY_FAILED\n')
                f.write('    copy /y "%BAK%" "%DST%" >nul\n')
                f.write('    start "" "%DST%" --post-update-result "%RES%"\n')
                f.write('    goto :cleanup\n')
                f.write(')\n')
                f.write(':healthy\n')
                f.write('del "%MARK%" 2>nul\n')
                f.write('del "%BAK%" 2>nul\n')
                f.write('del "%SRC%" 2>nul\n')
                f.write('goto :cleanup\n')
                f.write(':rollback\n')
                f.write('> "%RES%" echo UPDATED_ROLLBACK\n')
                f.write('> "%RESP%" echo UPDATED_ROLLBACK\n')
                f.write('copy /y "%BAK%" "%DST%" >nul\n')
                f.write('set "BAK_IS_313=0"\n')
                f.write('findstr /M /I /C:"python313.dll" "%BAK%" >nul 2>nul && set "BAK_IS_313=1"\n')
                f.write('if "%BAK_IS_313%"=="1" (\n')
                f.write('    rem Backup requires py313 runtime; skip auto-launch to avoid a second DLL error dialog.\n')
                f.write('    goto :cleanup\n')
                f.write(')\n')
                f.write('start "" "%DST%" --post-update-result "%RES%"\n')
                f.write(':cleanup\n')
                f.write('del "%~f0" 2>nul\n')
            if platform.system() == "Windows":
                # Always request elevation for replacement so update completes consistently on user systems.
                vbs = _os.path.join(td, "AutoBE_updater_elevate.vbs")
                batch_esc = batch.replace('"', '""')
                with open(vbs, 'w') as f:
                    f.write('CreateObject("Shell.Application").ShellExecute "cmd.exe", "/c ""' + batch_esc + '""", "", "runas", 0\n')
                subprocess.Popen(['wscript.exe', '//B', vbs], creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0x08000000))
            else:
                subprocess.Popen(['sh', '-c', f'sleep 2; cp "{new_exe}" "{current_exe}" && "{current_exe}" &'], creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0x08000000) if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0)
            sys.exit(0)
        except Exception as e:
            log_error(e)
            self._show_update_error(f"Install failed: {str(e)}")

    def _pick_installer_asset(self, release_data, expected_version=None):
        """Select installer asset (.exe setup) from release assets."""
        assets = (release_data or {}).get("assets") or []
        ver_norm = str(expected_version or "").strip().lstrip("vV")

        def _score(a):
            name = str((a or {}).get("name") or "").strip().lower()
            if not name.endswith(".exe"):
                return -1
            if not any(k in name for k in ("setup", "installer")):
                return -1
            score = 0
            if "autobe" in name:
                score += 200
            if "setup" in name:
                score += 120
            if "installer" in name:
                score += 80
            if ver_norm and ver_norm in name:
                score += 300
            try:
                score += min(int((a or {}).get("size") or 0) // (1024 * 1024), 150)
            except Exception:
                pass
            return score

        ranked = sorted(assets, key=_score, reverse=True)
        return ranked[0] if ranked and _score(ranked[0]) >= 0 else None

    def _offer_installer_fallback_update(self, release_data, expected_version, fail_message):
        """Offer installer-based fallback when in-place EXE update is blocked."""
        try:
            if getattr(self, "_installer_fallback_in_progress", False):
                return
            installer_asset = self._pick_installer_asset(release_data, expected_version=expected_version)
            if not installer_asset:
                self._show_update_error(fail_message)
                return
            ask = _messagebox.askyesno(
                _("update.failed"),
                f"{fail_message}\n\n"
                "AutoBE can download and run the installer update automatically instead.\n"
                "Do you want to continue with installer fallback?",
            )
            if not ask:
                self._show_update_error(fail_message)
                return
            self._installer_fallback_in_progress = True
            self._show_update_overlay_ui("Downloading installer fallback...")
            threading.Thread(
                target=self._download_and_run_installer_fallback,
                args=(installer_asset,),
                daemon=True,
            ).start()
        except Exception as e:
            log_error(e)
            self._show_update_error(fail_message)

    def _download_and_run_installer_fallback(self, installer_asset):
        """Download installer asset and run elevated in-place upgrade."""
        try:
            if GITHUB_TOKEN:
                download_url = installer_asset.get("url")
                if not download_url and installer_asset.get("id"):
                    download_url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/assets/{installer_asset['id']}"
            else:
                download_url = installer_asset.get("browser_download_url")
            if not download_url:
                raise RuntimeError("Installer fallback failed: no installer download URL.")
            headers = {"Accept": "application/octet-stream"}
            if GITHUB_TOKEN:
                headers["Authorization"] = f"token {GITHUB_TOKEN}"
            td = _tempfile.gettempdir()
            installer_path = _os.path.join(td, "AutoBE_update_setup.exe")
            r = _requests.get(download_url, headers=headers, timeout=90, stream=True, allow_redirects=True)
            r.raise_for_status()
            with open(installer_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            got = _os.path.getsize(installer_path) if _os.path.exists(installer_path) else 0
            exp = int(installer_asset.get("size") or 0)
            if got <= 0:
                raise RuntimeError("Installer fallback failed: downloaded installer is empty.")
            if exp > 0 and got != exp:
                raise RuntimeError(f"Installer fallback failed: size mismatch (expected {exp}, got {got}).")
            self._root.after(0, lambda: self._update_overlay_set_status("Launching installer update..."))
            self._root.after(300, lambda: self._run_installer_fallback_batch(installer_path, sys.executable))
        except Exception as e:
            log_error(e)
            self._installer_fallback_in_progress = False
            self._root.after(0, lambda: self._show_update_error(f"Installer fallback failed: {str(e)}"))

    def _run_installer_fallback_batch(self, installer_exe, current_exe):
        """Run installer as elevated upgrade, then relaunch app."""
        try:
            td = _tempfile.gettempdir()
            batch = _os.path.join(td, "AutoBE_installer_update.bat")
            with open(batch, "w", encoding="utf-8") as f:
                f.write("@echo off\n")
                f.write("setlocal EnableExtensions\n")
                f.write('set "INS=' + installer_exe.replace('"', '""') + '"\n')
                f.write('set "APP=' + current_exe.replace('"', '""') + '"\n')
                f.write("timeout /t 1 /nobreak >nul\n")
                f.write('start "" /wait "%INS%" /SP- /NORESTART /CLOSEAPPLICATIONS\n')
                f.write('if exist "%APP%" start "" "%APP%"\n')
                f.write('del "%INS%" 2>nul\n')
                f.write('del "%~f0" 2>nul\n')
            if platform.system() == "Windows":
                vbs = _os.path.join(td, "AutoBE_installer_update_elevate.vbs")
                batch_esc = batch.replace('"', '""')
                with open(vbs, "w", encoding="utf-8") as f:
                    f.write('CreateObject("Shell.Application").ShellExecute "cmd.exe", "/c ""' + batch_esc + '""", "", "runas", 0\n')
                subprocess.Popen(["wscript.exe", "//B", vbs], creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000))
            else:
                subprocess.Popen(["sh", "-c", f'"{installer_exe}" &'], creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000) if hasattr(subprocess, "CREATE_NO_WINDOW") else 0)
            sys.exit(0)
        except Exception as e:
            log_error(e)
            self._installer_fallback_in_progress = False
            self._show_update_error(f"Installer launch failed: {str(e)}")

    def _show_update_error(self, message):
        """Show themed error on update overlay with Close button. No browser."""
        self._update_overlay.grid()
        self._update_overlay.lift()
        for w in self._update_overlay.winfo_children():
            w.destroy()
        self._update_overlay.grid_columnconfigure(0, weight=1)
        self._update_overlay.grid_rowconfigure(0, weight=1)
        center = _tk.Frame(self._update_overlay, bg='#000000')
        center.place(relx=0.5, rely=0.5, anchor='center')
        _tk.Label(center, text=_("update.failed"), bg='#000000', fg='#ef4444', font=('Segoe UI', 18, 'bold')).pack(pady=(0, 16))
        _tk.Label(center, text=message, bg='#000000', fg='#e5e7eb', font=('Segoe UI', 10), justify='center', wraplength=360).pack(pady=(0, 24))
        def close():
            self._update_overlay.grid_remove()
        _tk.Button(center, text=_("common.close"), command=close, bg='#9333ea', fg='#FFFFFF', font=('Segoe UI', 11, 'bold'), relief='flat', cursor='hand2', activebackground='#a855f7', padx=32, pady=10).pack()

    def _check_activation(self):
        _hwid = self._generate_hwid()

        # Clear local cache files on reinstall to fix false bans
        self._clear_local_cache_files()

        try:
            # version.txt line 1 = minimum version allowed to run; line 2 = latest version for Check for updates.
            _version_text = self._fetch_github_file("version.txt")
            if _version_text:
                try:
                    _min_allowed = _version_text.strip().splitlines()[0].strip()
                    if self._version_tuple(APP_VERSION) < self._version_tuple(_min_allowed):
                        _messagebox.showerror(_("update.update_required_title"), _("update.update_required_msg"))
                        sys.exit()
                except Exception as e:
                    _logging.debug("Version check parse failed: %s", e)
            # If _version_text is None, network failed — skip version check (allow offline use)

            # --- Check blacklist from GitHub (or cached when offline) ---
            blacklist_text = self._fetch_github_file("blacklist.txt")
            if blacklist_text:
                self._save_blacklist_cache(blacklist_text)
                current_blacklist = set(line.strip() for line in blacklist_text.strip().splitlines() if line.strip())
                _hwid_in_block = _hwid in current_blacklist
                # If HWID is NOT in GitHub blacklist but IS in local cache, clear local cache (user was unbanned)
                if not _hwid_in_block:
                    blocked_hashes = self._load_cached_blacklist()
                    if self._block_hash(_hwid) in blocked_hashes:
                        # Clear local cache since user was unbanned on GitHub
                        try:
                            _os.remove(self._get_blacklist_cache_path())
                            _logging.info("Cleared local blacklist cache (HWID removed from GitHub)")
                        except Exception:
                            pass
            else:
                blocked_hashes = self._load_cached_blacklist()
                _hwid_in_block = self._block_hash(_hwid) in blocked_hashes
            if _hwid_in_block:
                # Show ban screen - ensure root is visible first
                if self._is_root_alive():
                    try:
                        self._root.deiconify()
                        self._root.update_idletasks()
                    except:
                        pass
                    self._root.after(100, lambda: self._show_ban_screen("You have been banned from using AutoBE."))
                else:
                    _messagebox.showerror(_("activation.denied"), _("msg.banned"))
                    sys.exit()
                return

            # --- Check for spoofed system / VM (Windows, Linux, macOS) ---
            # DISABLED: Spoofing detection causing false bans - too aggressive
            # spoofing_detected = self._detect_spoofing(_hwid)
            # if spoofing_detected:
            #     # Auto-add to GitHub blacklist + local cache (only when 2+ flags; reduces false positives)
            #     try:
            #         self._append_to_blacklist(_hwid)
            #     except Exception as e:
            #         log_error(f"Failed to add spoofer to blacklist: {e}")
            #     self._append_to_blacklist_cache(_hwid)
            #     denied_message = "Spoofed hardware detected.\nAccess denied."
            #     if self._is_root_alive():
            #         try:
            #             self._root.deiconify()
            #             self._root.update_idletasks()
            #         except Exception:
            #             pass
            #         self._root.after(100, lambda: self._show_denied_screen(denied_message))
            #     else:
            #         _messagebox.showerror(_("msg.spoofer_detected"), denied_message)
            #         sys.exit()

            # --- Check HWID whitelist from GitHub (we only check if *this* device's HWID is in it; never show or store other users' HWIDs) ---
            hwid_text = self._fetch_github_file("hwid_address.txt")
            if hwid_text:
                try:
                    valid_hwids = [h.strip() for h in hwid_text.splitlines() if h.strip()]
                    if _hwid in valid_hwids:
                        # Device binding: same HWID must be from same physical machine (detect HWID spoofing)
                        # DISABLED: Fingerprint check causing false bans - too aggressive
                        # hwid_h = self._block_hash(_hwid)
                        # current_fp = self._get_device_fingerprint()
                        # stored_fp = self._get_stored_fingerprint(hwid_h)
                        # if stored_fp is not None and stored_fp != current_fp:
                        #     self._deny_and_blacklist_spoofed_hwid(_hwid)
                        #     return
                        self._save_verified_hwid(_hwid)
                        # self._save_fingerprint_for_hwid(hwid_h, current_fp)
                        if self._is_root_alive():
                            self._root.after(0, self._unlock_application)
                        return
                except Exception as e:
                    _logging.debug("HWID whitelist parse failed: %s", e)

            # --- Offline (could not reach GitHub): only allow if *this* device's HWID was already verified on this machine (must have activated with WiFi first) ---
            if hwid_text is None:
                verified_hashes = self._load_verified_hwids()
                if self._block_hash(_hwid) in verified_hashes:
                    # Device binding: fingerprint must match the device that first activated this HWID
                    # DISABLED: Fingerprint check causing false bans - too aggressive
                    # hwid_h = self._block_hash(_hwid)
                    # current_fp = self._get_device_fingerprint()
                    # stored_fp = self._get_stored_fingerprint(hwid_h)
                    # if stored_fp is not None and stored_fp != current_fp:
                    #     self._deny_and_blacklist_spoofed_hwid(_hwid)
                    #     return
                    if self._is_root_alive():
                        self._root.after(0, self._unlock_application)
                    return
                # Not verified — require internet to verify
                if self._is_root_alive():
                    self._root.after(0, lambda: self._show_activation_window(offline=True))
                return

            # Online but not in whitelist — sync local memory: remove this device from verified so they can't use offline either; then show activation
            self._remove_verified_hwid(_hwid)
            if self._is_root_alive():
                self._root.after(0, self._show_activation_window)
                
        except Exception as e:
            _logging.error("Activation failed", exc_info=e)
            # Show activation window as fallback
            if self._is_root_alive():
                self._root.after(0, self._show_activation_window)

    def _show_ban_screen(self, ban_message):
        """Show ban screen overlay only when the player is found in the blacklist."""
        if not self._is_root_alive():
            return
        
        # Clear any existing widgets in ban overlay
        for widget in self._ban_overlay.winfo_children():
            widget.destroy()
        
        # Configure ban overlay
        self._ban_overlay.columnconfigure(0, weight=1)
        self._ban_overlay.rowconfigure(0, weight=1)
        
        # Main container
        container = _tk.Frame(self._ban_overlay, bg='#000000')
        container.grid(row=0, column=0, sticky="nsew")
        container.columnconfigure(0, weight=1)
        container.rowconfigure(1, weight=1)
        
        # Ban icon/header (using text as icon)
        icon_frame = _tk.Frame(container, bg='#000000')
        icon_frame.grid(row=0, column=0, pady=(80, 20))
        
        ban_icon = _tk.Label(
            icon_frame,
            text="🚫",
            bg='#000000',
            fg='#FF0000',
            font=("Segoe UI", 72, "bold")
        )
        ban_icon.pack()
        
        # Ban title
        title_label = _tk.Label(
            container,
            text=_("activation.denied"),
            bg='#000000',
            fg='#FF0000',
            font=("Segoe UI", 32, "bold")
        )
        title_label.grid(row=1, column=0, pady=(0, 20))
        
        # Ban message
        message_label = _tk.Label(
            container,
            text=ban_message,
            bg='#000000',
            fg='#FFFFFF',
            font=("Segoe UI", 14),
            justify='center',
            wraplength=600
        )
        message_label.grid(row=2, column=0, pady=(0, 30))
        
        # Additional info
        info_label = _tk.Label(
            container,
            text=_("activation.device_denied"),
            bg='#000000',
            fg='#888888',
            font=("Segoe UI", 11),
            justify='center'
        )
        info_label.grid(row=3, column=0, pady=(0, 40))
        
        # Close button
        close_button = _tk.Button(
            container,
            text=_("common.close"),
            command=self._root.destroy,
            bg='#1a1a1a',
            fg='#FFFFFF',
            font=("Segoe UI", 12, "bold"),
            relief='flat',
            cursor='hand2',
            activebackground='#2a2a2a',
            activeforeground='#FFFFFF',
            padx=40,
            pady=10,
            borderwidth=1,
            highlightthickness=1,
            highlightbackground='#FF0000',
            highlightcolor='#FF0000'
        )
        close_button.grid(row=4, column=0, pady=(0, 50))
        
        # Ensure root window is visible and on top
        try:
            self._root.deiconify()
            self._root.lift()
            self._root.focus_force()
            self._root.update_idletasks()
        except:
            pass
        
        # Show ban overlay (on top of everything)
        self._ban_overlay.tkraise()
        self._ban_overlay.grid()
        self._ban_overlay.update_idletasks()
        
        # Prevent window from being closed during ban screen
        self._root.protocol("WM_DELETE_WINDOW", lambda: None)
        
        # Auto-close after 10 seconds
        self._root.after(10000, self._root.destroy)

    def _show_denied_screen(self, message):
        """Show access-denied overlay (e.g. spoofing). Not the ban screen; ban is only for blacklist."""
        if not self._is_root_alive():
            return
        
        for widget in self._ban_overlay.winfo_children():
            widget.destroy()
        self._ban_overlay.columnconfigure(0, weight=1)
        self._ban_overlay.rowconfigure(0, weight=1)
        container = _tk.Frame(self._ban_overlay, bg='#000000')
        container.grid(row=0, column=0, sticky="nsew")
        container.columnconfigure(0, weight=1)
        container.rowconfigure(1, weight=1)
        icon_frame = _tk.Frame(container, bg='#000000')
        icon_frame.grid(row=0, column=0, pady=(80, 20))
        _tk.Label(icon_frame, text="⚠", bg='#000000', fg='#CC6600', font=("Segoe UI", 72, "bold")).pack()
        title = _("activation.access_denied") if _("activation.access_denied") != "activation.access_denied" else "Access denied"
        _tk.Label(container, text=title, bg='#000000', fg='#CC6600', font=("Segoe UI", 32, "bold")).grid(row=1, column=0, pady=(0, 20))
        _tk.Label(container, text=message, bg='#000000', fg='#FFFFFF', font=("Segoe UI", 14), justify='center', wraplength=600).grid(row=2, column=0, pady=(0, 30))
        _tk.Label(container, text=_("activation.device_denied"), bg='#000000', fg='#888888', font=("Segoe UI", 11), justify='center').grid(row=3, column=0, pady=(0, 40))
        close_btn = _tk.Button(container, text=_("common.close"), command=self._root.destroy, bg='#1a1a1a', fg='#FFFFFF', font=("Segoe UI", 12, "bold"), relief='flat', cursor='hand2', activebackground='#2a2a2a', activeforeground='#FFFFFF', padx=40, pady=10, borderwidth=1, highlightthickness=1, highlightbackground='#CC6600', highlightcolor='#CC6600')
        close_btn.grid(row=4, column=0, pady=(0, 50))
        try:
            self._root.deiconify()
            self._root.lift()
            self._root.focus_force()
            self._root.update_idletasks()
        except Exception:
            pass
        self._ban_overlay.tkraise()
        self._ban_overlay.grid()
        self._ban_overlay.update_idletasks()
        self._root.protocol("WM_DELETE_WINDOW", lambda: None)
        self._root.after(10000, self._root.destroy)
    
    def _create_activation_overlay(self):
        """Create the activation overlay UI in the main window."""
        if not self._is_root_alive():
            return
        
        # Ensure root is visible
        try:
            self._root.deiconify()
        except:
            pass
            
        # Clear any existing widgets in the overlay
        for widget in self._activation_overlay.winfo_children():
            widget.destroy()
        
        # Create centered container with modern styling
        center_frame = _tk.Frame(self._activation_overlay, bg='#000000')
        center_frame.place(relx=0.5, rely=0.5, anchor='center')
        
        # Modern lock icon with subtle glow effect
        lock_label = _tk.Label(
            center_frame,
            text="🔒",
            bg='#000000',
            fg='#A50CAC',
            font=("Segoe UI", 56, "bold")
        )
        lock_label.pack(pady=(0, 40))
        
        # Instructions with modern typography
        instruction_label = _tk.Label(
            center_frame,
            text=_("activation.enter_key_title"),
            bg='#000000',
            fg='#FFFFFF',
            font=("Segoe UI", 16, "normal")
        )
        instruction_label.pack(pady=(0, 25))
        if getattr(self, '_activation_offline', False):
            offline_label = _tk.Label(
                center_frame,
                text=_("activation.offline_verify") if _("activation.offline_verify") != "activation.offline_verify" else "Connect to the internet to verify.",
                bg='#000000',
                fg='#A50CAC',
                font=("Segoe UI", 12, "normal")
            )
            offline_label.pack(pady=(0, 15))
        
        # Modern entry field - pure black, no borders
        self._activation_entry = _tk.Entry(
            center_frame,
            width=45,
            bg='#000000',
            fg='#FFFFFF',
            font=("Segoe UI", 13),
            insertbackground='#A50CAC',
            relief=_tk.FLAT,
            bd=0,
            highlightthickness=0
        )
        self._activation_entry.pack(pady=10, padx=20, ipady=8)
        self._activation_entry.focus()
        
        # Bind Enter key to submit
        self._activation_entry.bind('<Return>', lambda e: self._submit_activation_key())
        
        # Modern submit button with hover effect
        submit_btn = _tk.Button(
            center_frame,
            text=_("activation.activate"),
            command=self._submit_activation_key,
            bg='#A50CAC',
            fg='#FFFFFF',
            font=("Segoe UI", 13, "bold"),
            relief=_tk.FLAT,
            bd=0,
            cursor="hand2",
            activebackground='#8B0A9C',
            activeforeground='#FFFFFF',
            padx=40,
            pady=12,
            highlightthickness=0
        )
        submit_btn.pack(pady=(20, 10))
        
        # Error label with modern styling
        self._activation_error_label = _tk.Label(
            center_frame,
            text="",
            bg='#000000',
            fg='#FF6B6B',
            font=("Segoe UI", 11)
        )
        self._activation_error_label.pack(pady=(5, 0))
        
        # Show the overlay
        self._activation_overlay.tkraise()
    
    def _show_loading_animation(self, wait_seconds=120):
        """Show RGB loading animation while processing activation."""
        if not self._is_root_alive():
            return
        
        # Set loading state to prevent closing
        self._is_loading = True
            
        # Clear any existing widgets in the overlay
        for widget in self._activation_overlay.winfo_children():
            widget.destroy()
        
        # Create centered container
        center_frame = _tk.Frame(self._activation_overlay, bg='#000000')
        center_frame.place(relx=0.5, rely=0.5, anchor='center')
        
        # Title
        title_label = _tk.Label(
            center_frame,
            text=_("activation.processing"),
            bg='#000000',
            fg='#FFFFFF',
            font=("Segoe UI", 20, "bold")
        )
        title_label.pack(pady=(0, 40))
        
        # Loading spinner container
        spinner_frame = _tk.Frame(center_frame, bg='#000000')
        spinner_frame.pack(pady=20)
        
        # Create multiple spinning circles for RGB effect
        self._loading_dots = []
        dot_colors = ['#FF0000', '#00FF00', '#0000FF', '#FFFF00', '#FF00FF', '#00FFFF']
        for i in range(6):
            dot = _tk.Label(
                spinner_frame,
                text="●",
                bg='#000000',
                fg=dot_colors[i],
                font=("Segoe UI", 24, "bold")
            )
            dot.pack(side=_tk.LEFT, padx=5)
            self._loading_dots.append(dot)
        
        # Status text
        self._loading_status_label = _tk.Label(
            center_frame,
            text=_("activation.syncing"),
            bg='#000000',
            fg='#A50CAC',
            font=("Segoe UI", 12)
        )
        self._loading_status_label.pack(pady=30)
        
        # Progress counter
        self._loading_progress_label = _tk.Label(
            center_frame,
            text="",
            bg='#000000',
            fg='#CCCCCC',
            font=("Segoe UI", 11)
        )
        self._loading_progress_label.pack(pady=10)
        
        # Store animation state
        self._loading_animation_step = 0
        self._loading_wait_remaining = wait_seconds
        self._loading_animation_id = None
        
        # Start animation
        self._loading_status_messages = [
            _("activation.syncing"),
            _("activation.processing_key"),
            _("activation.updating_db"),
            _("activation.finalizing"),
            _("activation.almost_done")
        ]
        self._loading_status_index = 0
        
        # Update progress label
        self._loading_progress_label.config(text=_f("activation.please_wait_seconds", seconds=wait_seconds))
        
        # Start the RGB animation
        self._animate_loading_rgb()
        
        # Start countdown
        self._loading_countdown()
    
    def _animate_loading_rgb(self):
        """Animate RGB colors in the loading dots."""
        if not self._is_root_alive() or not hasattr(self, '_loading_dots'):
            return
        
        # RGB color cycling
        step = self._loading_animation_step
        
        for i, dot in enumerate(self._loading_dots):
            # Create RGB color wave effect
            phase = (step + i * 60) % 360
            r = int(127.5 * (1 + math.sin(math.radians(phase))))
            g = int(127.5 * (1 + math.sin(math.radians(phase + 120))))
            b = int(127.5 * (1 + math.sin(math.radians(phase + 240))))
            
            color = f"#{r:02x}{g:02x}{b:02x}"
            dot.config(fg=color)
        
        # Update status message periodically
        if step % 30 == 0 and hasattr(self, '_loading_status_label'):
            self._loading_status_label.config(
                text=self._loading_status_messages[self._loading_status_index % len(self._loading_status_messages)]
            )
            self._loading_status_index += 1
        
        self._loading_animation_step += 5
        self._loading_animation_id = self._root.after(50, self._animate_loading_rgb)
    
    def _loading_countdown(self):
        """Countdown timer for loading."""
        if not self._is_root_alive() or not hasattr(self, '_loading_wait_remaining'):
            return
        
        if self._loading_wait_remaining > 0:
            minutes = self._loading_wait_remaining // 60
            seconds = self._loading_wait_remaining % 60
            if minutes > 0:
                time_text = _f("activation.please_wait_min_sec", minutes=minutes, seconds=seconds)
            else:
                time_text = _f("activation.please_wait_sec", seconds=seconds)
            
            if hasattr(self, '_loading_progress_label'):
                self._loading_progress_label.config(text=time_text)
            
            self._loading_wait_remaining -= 1
            self._root.after(1000, self._loading_countdown)
        else:
            # Stop animation and unlock
            if hasattr(self, '_loading_animation_id') and self._loading_animation_id:
                self._root.after_cancel(self._loading_animation_id)
            
            # Clean up loading state
            if hasattr(self, '_loading_dots'):
                del self._loading_dots
            if hasattr(self, '_loading_animation_step'):
                del self._loading_animation_step
            
            # Re-enable window closing
            self._is_loading = False
            
            # Unlock the application
            self._unlock_application()
        
    def _show_activation_window(self, offline=False):
        """Show activation overlay in the main window. If offline=True, show message that internet is required to verify."""
        if not self._is_root_alive():
            return
        
        self._activation_offline = bool(offline)
        # Ensure root window is visible (in case it was withdrawn)
        self._root.deiconify()
        self._root.lift()
        self._root.focus_force()
        self._root.update_idletasks()
        self._root.update()
        
        # Ensure overlay is visible and on top
        self._activation_overlay.grid()
        self._activation_overlay.tkraise()
        
        # Hide notebook if it's visible
        self.notebook.grid_remove()
        
        self._create_activation_overlay()
        
        # Force update after creating overlay
        self._root.update_idletasks()
        self._root.update()
        
        _logging.debug('Activation overlay displayed.')
    
    def _submit_activation_key(self):
        """Handle activation key submission."""
        if not hasattr(self, '_activation_entry'):
            return
            
        _key = self._activation_entry.get().strip()

        if not _key:
            if hasattr(self, '_activation_error_label'):
                self._activation_error_label.config(text=_("activation.enter_key_error"))
            return

        _url_keys = "https://raw.githubusercontent.com/FrostyHostMC/AutoBE/main/keys.csv"
        _headers = {
            "Authorization": f"token {GITHUB_TOKEN}"
        }

        try:
            # Clear error message
            if hasattr(self, '_activation_error_label'):
                self._activation_error_label.config(text="")
            
            # Fetch the current list of valid keys using the helper function
            keys_text = self._fetch_github_file("keys.csv")
            if keys_text is None:
                if hasattr(self, '_activation_error_label'):
                    self._activation_error_label.config(text=_("msg.connection_error") if _("msg.connection_error") != "msg.connection_error" else "Cannot reach server. Check your internet connection.")
                return
            response_text = keys_text
            
            # Parse CSV - try multiple methods to handle various formats
            valid_keys = []
            
            # Method 1: Try CSV reader (handles quoted values)
            try:
                csv_reader = csv.reader(io.StringIO(response_text), quoting=csv.QUOTE_MINIMAL)
                for row in csv_reader:
                    for key in row:
                        key = key.strip()
                        # Normalize key: remove spaces (consistent with input normalization)
                        key_normalized = key.replace(' ', '')
                        if key_normalized:
                            valid_keys.append(key_normalized)
            except Exception as e:
                log_error(f"CSV reader failed: {e}")
            
            # Method 2: Also try simple line-by-line parsing (in case CSV format is different)
            if not valid_keys:
                for line in response_text.splitlines():
                    line = line.strip()
                    if line:
                        # Remove CSV quotes if present
                        if line.startswith('"') and line.endswith('"'):
                            line = line[1:-1]
                        # Handle escaped quotes
                        line = line.replace('""', '"')
                        # Normalize: remove spaces
                        key_normalized = line.replace(' ', '')
                        if key_normalized:
                            valid_keys.append(key_normalized)
            
            # Remove any spaces from input key (in case user accidentally added spaces when pasting)
            normalized_input = _key.strip().replace(' ', '')
            
            # Debug logging
            _logging.debug(f"Looking for key: {normalized_input}")
            _logging.debug(f"Found {len(valid_keys)} keys in CSV")
            if len(valid_keys) <= 10:  # Only log if reasonable number
                _logging.debug(f"Valid keys: {valid_keys}")

            # Try exact match first
            if normalized_input not in valid_keys:
                # Try case-insensitive match (in case there's a case mismatch)
                normalized_lower = normalized_input.lower()
                matched_key = None
                for key in valid_keys:
                    if key.lower() == normalized_lower:
                        matched_key = key
                        break
                
                if matched_key:
                    # Use the matched key (preserve original case from CSV)
                    normalized_input = matched_key
                else:
                    if hasattr(self, '_activation_error_label'):
                        self._activation_error_label.config(text=_("activation.invalid_key"))
                    return

            # Remove the key from keys.csv (use normalized key)
            valid_keys.remove(normalized_input)
            self._update_keys_csv(valid_keys)

            _hwid = self._generate_hwid()
            self._append_hwid(_hwid)
            self._save_verified_hwid(_hwid)

            # Send notification
            self._send_discord_notification(_key)
            
            # Show loading animation and wait for GitHub processing
            self._show_loading_animation(120)  # 2 minutes (120 seconds)

        except Exception as e:
            log_error(e)
            error_msg = f"Failed to validate key. Error: {str(e)}"
            if hasattr(self, '_activation_error_label'):
                self._activation_error_label.config(text=error_msg)
            else:
                _messagebox.showerror(_("msg.error"), error_msg)
    
    def _unlock_application(self):
        """Hide activation overlay and show the main application."""
        if not self._is_root_alive():
            return

        # Show terms BEFORE showing main content to prevent both windows being visible
        self._show_terms()

        # Hide activation overlay
        self._activation_overlay.grid_remove()

        # Show the notebook (main application)
        self.notebook.grid()

        # Create settings icon button integrated into notebook

        # Create widgets
        self._create_widgets()
        # Copy MUSIC_CREDITS.txt to .autobe folder so user has the YouTube credit link (non-blocking, safe)
        try:
            self._ensure_music_credits_file()
        except Exception:
            pass
        # Start background music once main screen is ready; try soon and retry if mixer not ready
        def _start_music_then_retry_if_silent():
            self._start_background_music()
            def _retry_if_not_playing(delay_next=2500):
                if not getattr(self, "_root", None) or not self._root.winfo_exists():
                    return
                if not getattr(self, "background_music_var", None) or not self.background_music_var.get():
                    return
                try:
                    if _PYGAME_MIXER_AVAILABLE and _pygame and _pygame.mixer.get_init() and not _pygame.mixer.music.get_busy():
                        self._start_background_music()
                    if delay_next and delay_next <= 6000:
                        self._root.after(delay_next, lambda dn=delay_next + 2500: _retry_if_not_playing(dn))
                except Exception:
                    pass
            self._root.after(2500, lambda: _retry_if_not_playing(2500))
        self._root.after(400, _start_music_then_retry_if_silent)
        self._root.after(900, _start_music_then_retry_if_silent)
        
        # Update Discord presence
        self._update_discord_presence(tab_name="AutoBE")
        
        # Auto-check for new release after delay (only prompts if update exists; delay avoids popup while opening Settings)
        self._root.after(6000, self._auto_check_for_updates)
        # Re-check periodically so the app always knows about new releases (silent when up to date)
        self._root.after(UPDATE_CHECK_INTERVAL_MS, self._periodic_update_check)
        # Show update outcome notice after UI has stabilized.
        self._root.after(1200, self._show_post_update_result_notice)
        # Keep Windows "Installed apps" version in sync after in-app exe updates.
        self._root.after(1500, self._sync_windows_uninstall_metadata)
        
        _logging.debug('Application unlocked.')

    def _show_post_update_result_notice(self):
        """If updater provided a result marker, show a one-time status dialog."""
        try:
            result = (getattr(self, "_pending_update_result", None) or "").strip().lower()
            if not result:
                return
            self._pending_update_result = None
            if result == "updated_ok":
                self._show_themed_info_dialog(
                    _("update.title"),
                    "Update completed successfully.\nYou are now running the new version.",
                    topmost=True,
                )
            elif result == "updated_rollback":
                self._show_themed_info_dialog(
                    _("update.failed"),
                    "Update could not start correctly, so AutoBE automatically rolled back to the previous version.",
                    topmost=True,
                )
            elif result == "updated_copy_failed":
                self._show_themed_info_dialog(
                    _("update.failed"),
                    "Update installation failed while replacing files.\nAutoBE kept your previous installed version.",
                    topmost=True,
                )
        except Exception:
            pass

    def _sync_windows_uninstall_metadata(self):
        """Sync uninstall DisplayName/DisplayVersion so Windows Apps list reflects current APP_VERSION."""
        if platform.system() != "Windows" or _winreg is None:
            return
        targets = [
            (_winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Uninstall"),
            (_winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Uninstall"),
            (_winreg.HKEY_LOCAL_MACHINE, r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
        ]
        desired_name = f"AutoBE version {APP_VERSION}"
        for root, base_path in targets:
            try:
                with _winreg.OpenKey(root, base_path, 0, _winreg.KEY_READ | _winreg.KEY_WRITE) as base:
                    i = 0
                    while True:
                        try:
                            subkey_name = _winreg.EnumKey(base, i)
                            i += 1
                        except OSError:
                            break
                        try:
                            with _winreg.OpenKey(base, subkey_name, 0, _winreg.KEY_READ | _winreg.KEY_WRITE) as sub:
                                try:
                                    display_name, _ = _winreg.QueryValueEx(sub, "DisplayName")
                                except Exception:
                                    continue
                                dn = str(display_name or "").lower()
                                if "autobe" not in dn:
                                    continue
                                try:
                                    _winreg.SetValueEx(sub, "DisplayVersion", 0, _winreg.REG_SZ, APP_VERSION)
                                except Exception:
                                    pass
                                # Keep naming style consistent with installer default style.
                                try:
                                    _winreg.SetValueEx(sub, "DisplayName", 0, _winreg.REG_SZ, desired_name)
                                except Exception:
                                    pass
                        except Exception:
                            continue
            except Exception:
                continue
    
    def _update_keys_csv(self, valid_keys):
        """Update the keys.csv file by removing the used key"""
        _keys_file_url = "https://api.github.com/repos/FrostyHostMC/AutoBE/contents/keys.csv"
        _headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Content-Type": "application/json"
        }
        # Recreate the keys.csv content using proper CSV formatting
        output = io.StringIO()
        csv_writer = csv.writer(output)
        # Write each key as a separate row (properly handles special characters)
        for key in valid_keys:
            csv_writer.writerow([key])
        new_content = output.getvalue().encode('utf-8')
        
        # Base64 encode the content
        encoded_content = base64.b64encode(new_content).decode('utf-8')
        
        try:
            # Get the SHA of the current file
            response = _requests.get(_keys_file_url, headers=_headers)
            response.raise_for_status()
            sha = response.json()['sha']

            # Update the file on GitHub with the new content
            update_data = {
                "message": "Remove used activation key",
                "content": encoded_content,
                "sha": sha
            }
            response = _requests.put(_keys_file_url, json=update_data, headers=_headers)
            response.raise_for_status()
        except Exception as e:
            log_error(e)
            raise Exception(f"Failed to update keys.csv: {str(e)}")

    def _append_to_blacklist(self, _hwid):
        """Append HWID to the blacklist on GitHub"""
        blacklist_file_url = "https://api.github.com/repos/FrostyHostMC/AutoBE/contents/blacklist.txt"
        _headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Content-Type": "application/json"
        }
        try:
            response = _requests.get(blacklist_file_url, headers=_headers)
            response.raise_for_status()
            
            file_data = response.json()
            current_content = base64.b64decode(file_data['content']).decode('utf-8').rstrip()
            sha = file_data['sha']

            # Check if HWID already in blacklist
            if _hwid in current_content:
                return  # Already banned
            
            updated_content = f"{current_content}\n{_hwid}\n" if current_content else f"{_hwid}\n"
            encoded_content = base64.b64encode(updated_content.encode('utf-8')).decode('utf-8')
            
            update_data = {
                "message": "Auto-ban spoofer",
                "content": encoded_content,
                "sha": sha
            }
            put_response = _requests.put(blacklist_file_url, json=update_data, headers=_headers)
            put_response.raise_for_status()
            
            return put_response.json()

        except _requests.exceptions.RequestException as req_err:
            log_error(f"Failed to append to blacklist: {req_err}")
            raise
    
    def _detect_spoofing(self, _hwid):
        """Detect hardware spoofing / VM using multiple checks on Windows, Linux, and macOS. Returns True if detected."""
        spoofing_flags = []
        try:
            # Computer name / hostname (all platforms) - VM patterns
            try:
                computer_name = platform.node().lower()
                vm_patterns = ["vmware", "virtualbox", "vbox", "qemu", "xen", "kvm", "parallels", "bochs", "innotek", "hyper-v", "hyperv"]
                if any(pattern in computer_name for pattern in vm_patterns):
                    spoofing_flags.append("vm_computer_name")
            except Exception:
                pass
            
            if platform.system() == "Windows":
                # --- Windows: WMIC / getmac checks ---
                try:
                    output = subprocess.check_output(
                        ["wmic", "baseboard", "get", "serialnumber"],
                        stderr=subprocess.STDOUT,
                        text=True,
                        timeout=5
                    ).splitlines()
                    serial = next(
                        (line.strip().lower() for line in output if line.strip() and "serialnumber" not in line.lower()),
                        ""
                    )
                    generic_serials = ["to be filled by o.e.m.", "", "default string", "oem", "default", "system serial number"]
                    if serial in generic_serials:
                        spoofing_flags.append("generic_motherboard_serial")
                except Exception:
                    pass
                try:
                    output = subprocess.check_output(
                        ["wmic", "cpu", "get", "processorid"],
                        stderr=subprocess.STDOUT,
                        text=True,
                        timeout=5
                    ).splitlines()
                    cpu_id = next(
                        (line.strip().lower() for line in output if line.strip() and "processorid" not in line.lower()),
                        ""
                    )
                    if not cpu_id or cpu_id == "0000000000000000" or len(cpu_id) < 8:
                        spoofing_flags.append("invalid_cpu_id")
                except Exception:
                    pass
                try:
                    output = subprocess.check_output(
                        ["wmic", "diskdrive", "get", "serialnumber"],
                        stderr=subprocess.STDOUT,
                        text=True,
                        timeout=5
                    ).splitlines()
                    disk_serials = [line.strip().lower() for line in output if line.strip() and "serialnumber" not in line.lower()]
                    # Only flag when ALL disks have generic serials (one USB/secondary drive with no serial is common on real PCs)
                    if disk_serials and all(s in ["", "none", "00000000"] for s in disk_serials):
                        spoofing_flags.append("generic_disk_serial")
                except Exception:
                    pass
                # Check system manufacturer/model for VM *before* getmac so we can avoid false positives from Hyper-V/Docker/WSL2 virtual NICs on real PCs
                # Note: "microsoft corporation" and "oracle" omitted — real Surface/OEM and Oracle servers report these
                try:
                    out = subprocess.check_output(
                        ["wmic", "computersystem", "get", "manufacturer,model"],
                        stderr=subprocess.STDOUT,
                        text=True,
                        timeout=5
                    ).lower()
                    vm_manufacturer = ["vmware", "virtualbox", "vbox", "qemu", "xen", "innotek", "parallels", "bochs"]
                    if any(m in out for m in vm_manufacturer):
                        spoofing_flags.append("vm_system_manufacturer")
                except Exception:
                    pass
                try:
                    output = subprocess.check_output(
                        ["getmac", "/fo", "csv", "/nh"],
                        stderr=subprocess.STDOUT,
                        text=True,
                        timeout=5
                    )
                    # Only flag VM MAC if we already have a VM indicator (manufacturer or computer name).
                    # Real PCs often have Hyper-V/Docker/WSL2 virtual adapters with VM MACs — avoid false bans.
                    # Also exclude VPN adapters (NordVPN, ExpressVPN, etc. use virtual NICs with similar MAC ranges)
                    vm_mac_prefixes = ["00-05-69", "00-0c-29", "00-50-56", "08-00-27", "00-15-5d", "00:05:69", "00:0c:29", "00:50:56", "08:00:27", "00:15:5d"]
                    # VPN adapter names to exclude (case-insensitive)
                    vpn_adapter_names = ["nordvpn", "expressvpn", "surfshark", "cyberghost", "private internet access", "pia", "protonvpn", "windscribe", "tunnelbear", "hotspot shield", "vpn"]
                    output_lower = output.lower()
                    has_vm_mac = any(prefix.lower() in output_lower for prefix in vm_mac_prefixes)
                    has_vpn_adapter = any(vpn_name in output_lower for vpn_name in vpn_adapter_names)
                    if has_vm_mac and not has_vpn_adapter:
                        if "vm_system_manufacturer" in spoofing_flags or "vm_computer_name" in spoofing_flags:
                            spoofing_flags.append("vm_mac_address")
                except Exception:
                    pass
                try:
                    output = subprocess.check_output(
                        ["wmic", "bios", "get", "version"],
                        stderr=subprocess.STDOUT,
                        text=True,
                        timeout=5
                    ).splitlines()
                    bios_version = next(
                        (line.strip().lower() for line in output if line.strip() and "version" not in line.lower()),
                        ""
                    )
                    # "bios" alone is too generic — many real BIOSes report it; only flag clearly placeholder values
                    if bios_version in ["default", "system bios", ""]:
                        spoofing_flags.append("generic_bios")
                except Exception:
                    pass
                # --- Windows: VM video controller (VMware SVGA, VirtualBox Graphics, VirtIO, etc.) ---
                try:
                    output = subprocess.check_output(
                        ["wmic", "path", "win32_videocontroller", "get", "name"],
                        stderr=subprocess.STDOUT,
                        text=True,
                        timeout=5
                    ).lower()
                    vm_video_keywords = ["vmware", "virtualbox", "vbox", "qemu", "parallels", "virtio", "red hat virtio", "vmware svga", "virtualbox graphics", "bochs"]
                    if any(kw in output for kw in vm_video_keywords):
                        spoofing_flags.append("vm_video_controller")
                except Exception:
                    pass
                # --- Windows: HypervisorPresent (guest often reports True; host with Hyper-V can too, so just one extra signal) ---
                try:
                    output = subprocess.check_output(
                        ["wmic", "computersystem", "get", "hypervisorpresent"],
                        stderr=subprocess.STDOUT,
                        text=True,
                        timeout=5
                    ).lower()
                    if "true" in output and ("vm_system_manufacturer" in spoofing_flags or "vm_computer_name" in spoofing_flags or "vm_video_controller" in spoofing_flags):
                        spoofing_flags.append("win_hypervisor_present")
                except Exception:
                    pass
            
            elif platform.system() == "Linux":
                # --- Linux: containers (Docker/Podman etc.) = not real hardware ---
                try:
                    if _os.path.isfile("/.dockerenv") or _os.path.isfile("/run/.containerenv"):
                        spoofing_flags.append("linux_container")
                except Exception:
                    pass
                # --- Linux: hypervisor, DMI, and VM MAC checks ---
                try:
                    with open("/proc/cpuinfo", "r", encoding="utf-8", errors="ignore") as f:
                        cpuinfo = f.read().lower()
                    if "hypervisor" in cpuinfo:
                        spoofing_flags.append("linux_hypervisor")
                except Exception:
                    pass
                # DMI/sysfs: product name, sys_vendor, board_vendor often expose VM/cloud
                vm_dmi_keywords = [
                    "vmware", "virtualbox", "vbox", "qemu", "xen", "kvm", "innotek", "bochs",
                    "amazon ec2", "parallels", "openstack", "innotek gmbh",
                    "google compute engine", "digitalocean", "linode", "vultr", "oracle vm",
                    "red hat openstack", "rhev", "kvm/rhel", "openstack foundation"
                ]
                try:
                    dmi_base = "/sys/class/dmi/id"
                    for name in ["product_name", "sys_vendor", "board_vendor", "bios_vendor", "product_family"]:
                        path = _os.path.join(dmi_base, name)
                        if _os.path.isfile(path):
                            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                                val = f.read().strip().lower()
                            if any(kw in val for kw in vm_dmi_keywords):
                                spoofing_flags.append("linux_vm_dmi")
                                break
                except Exception:
                    pass
                # MAC addresses: virtual NIC prefixes (VMware, VirtualBox, QEMU/KVM, Hyper-V, Parallels)
                vm_mac_prefixes_linux = [
                    "00:05:69", "00:0c:29", "00:50:56", "08:00:27", "00:15:5d", "52:54:00",
                    "0a:00:27", "02:00:00", "00:1c:42", "00:03:ff", "00:0d:3a", "00:22:aa"
                ]
                try:
                    net_path = "/sys/class/net"
                    if _os.path.isdir(net_path):
                        for iface in _os.listdir(net_path):
                            if iface in ("lo", "bonding_masters"):
                                continue
                            addr_path = _os.path.join(net_path, iface, "address")
                            if _os.path.isfile(addr_path):
                                with open(addr_path, "r", encoding="utf-8", errors="ignore") as f:
                                    mac = f.read().strip().lower().replace("-", ":")
                                if any(mac.startswith(p.replace("-", ":")) for p in vm_mac_prefixes_linux):
                                    spoofing_flags.append("linux_vm_mac")
                                    break
                except Exception:
                    pass
                # --- Linux: systemd-detect-virt (reliable VM/container detection when available) ---
                try:
                    out = subprocess.check_output(
                        ["systemd-detect-virt"],
                        stderr=subprocess.DEVNULL,
                        text=True,
                        timeout=3
                    ).strip().lower()
                    # "none" = bare metal; "container" already covered by .dockerenv/.containerenv; anything else is VM or container
                    if out and out != "none":
                        spoofing_flags.append("linux_systemd_virt")
                except (FileNotFoundError, subprocess.CalledProcessError, OSError):
                    pass
                except Exception:
                    pass
                # --- Linux: virtio devices (strong VM indicator; rare on real hardware) ---
                try:
                    virtio_path = "/sys/bus/virtio/devices"
                    if _os.path.isdir(virtio_path) and len(_os.listdir(virtio_path)) > 0:
                        spoofing_flags.append("linux_virtio_devices")
                except Exception:
                    pass
            
            elif platform.system() == "Darwin":
                # --- macOS: VM detection via system_profiler or model identifier ---
                try:
                    out = subprocess.check_output(
                        ["system_profiler", "SPHardwareDataType"],
                        stderr=subprocess.DEVNULL,
                        text=True,
                        timeout=10
                    ).lower()
                    if "vmware" in out or "parallels" in out or "virtualbox" in out or "vbox" in out:
                        spoofing_flags.append("macos_vm")
                except Exception:
                    pass
                try:
                    # Model identifier often contains VM name on macOS VMs
                    out = subprocess.check_output(
                        ["sysctl", "-n", "hw.model"],
                        stderr=subprocess.DEVNULL,
                        text=True,
                        timeout=5
                    ).lower()
                    if "vmware" in out or "parallels" in out or "virtualbox" in out or "vbox" in out:
                        spoofing_flags.append("macos_vm")
                except Exception:
                    pass
                # --- macOS: ioreg can expose VM vendor strings even when system_profiler is spoofed ---
                try:
                    out = subprocess.check_output(
                        ["ioreg", "-l"],
                        stderr=subprocess.DEVNULL,
                        text=True,
                        timeout=5
                    ).lower()
                    if "vmware" in out or "parallels" in out or "virtualbox" in out or "innotek" in out or "vbox" in out:
                        spoofing_flags.append("macos_ioreg_vm")
                except Exception:
                    pass
            
            # Block only when we have strong evidence: require at least 5 indicators AND at least 1 VM-specific indicator
            # to avoid false positives (many real PCs have generic OEM serials, Hyper-V/Docker NICs, etc.)
            # VM-specific indicators: vm_computer_name, vm_system_manufacturer, vm_video_controller, vm_mac_address,
            # linux_container, linux_hypervisor, linux_vm_dmi, linux_vm_mac, linux_systemd_virt, linux_virtio_devices,
            # macos_vm, macos_ioreg_vm
            vm_specific_flags = [f for f in spoofing_flags if f.startswith(('vm_', 'linux_', 'macos_'))]
            if len(spoofing_flags) >= 5 and len(vm_specific_flags) >= 1:
                log_message = f"Spoofing/VM detected - Flags: {', '.join(spoofing_flags)}, HWID: {_hwid}"
                _logging.warning(log_message)
                log_error(log_message)
                return True
            
        except Exception as e:
            log_error(f"Spoofing detection error: {e}")
            return False
        
        return False
    
    def _append_hwid(self, _hwid):
        """Append HWID to the whitelist on GitHub"""
        _hwid_file_url = "https://api.github.com/repos/FrostyHostMC/AutoBE/contents/hwid_address.txt"
        _headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Content-Type": "application/json"
        }
        try:
            response = _requests.get(_hwid_file_url, headers=_headers)
            response.raise_for_status()
            
            file_data = response.json()
            current_content = base64.b64decode(file_data['content']).decode('utf-8').rstrip()
            sha = file_data['sha']

            updated_content = f"{current_content}\n{_hwid}\n"
            encoded_content = base64.b64encode(updated_content.encode('utf-8')).decode('utf-8')
            
            update_data = {
                "message": "Add new HWID",
                "content": encoded_content,
                "sha": sha
            }
            put_response = _requests.put(_hwid_file_url, json=update_data, headers=_headers)
            put_response.raise_for_status()
            
            return put_response.json()

        except _requests.exceptions.RequestException as req_err:
            log_error(req_err)
            raise Exception(f"HTTP request failed: {str(req_err)}")
        except Exception as e:
            log_error(e)
            raise Exception(f"Failed to update hwid_address.txt: {str(e)}")

    def _send_discord_notification(self, _key):
        """Send activation notification to Discord"""
        _hwid = self._generate_hwid()
        _webhook_url = "https://discord.com/api/webhooks/1279960853969502248/Y7VR7m6qEEe0UScvkZLe1IJO4lK-p7AP8_RAoXsWbsbrBui_geLnA_DW1TFJvvEA-ptg"
        _data = {
            "content": f"Activation key used: {_key}\nHWID: {_hwid}"
        }
        _requests.post(_webhook_url, json=_data)
        
    def _show_terms(self):
        # Main window is already hidden from __init__
        # Create terms window
        self._terms_window = _T1(self._root)
        self._root.wait_window(self._terms_window._w1)
        _logging.debug('Terms of Use window closed.')
        # Show main window after terms are accepted with smooth transition
        self._root.deiconify()
        self._root.lift()
        self._root.focus_force()
        self._root.update_idletasks()
        # Apply taskbar button fix after showing main window
        # Single attempt with minimal delay to reduce flickering
        self._root.after(150, lambda: _force_taskbar_button(self._root))
        self._root.after(300, lambda: self._apply_window_icon(self._root))

    def _create_widgets(self):
        # Create widgets inside the App1 Tab (app1_frame) - Modern styling
        # Configure app1_frame for proper resizing
        self.app1_frame.grid_columnconfigure(0, weight=1)
        self.app1_frame.grid_rowconfigure(0, weight=1, minsize=340)  # Files frame - expandable
        self.app1_frame.grid_rowconfigure(1, weight=0)  # Output frame - fixed
        self.app1_frame.grid_rowconfigure(2, weight=0)  # Buttons frame - fixed
        self.app1_frame.grid_rowconfigure(3, weight=0)  # Progress frame - fixed (don't shrink)
        
        self._frame_files = _tk.LabelFrame(self.app1_frame, text="📦 " + _("app.select_mcpacks"), bg='#1a1a1a', fg='#FFFFFF', font=("Segoe UI", 13, "bold"))
        self._frame_files.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")

        # File list: (display_name, path, photo_or_none) per item; photo refs kept to avoid GC
        self._file_list_data = []
        self._file_list_photo_refs = []
        self._file_list_selected = set()
        self._file_paths = {}
        self._files = []

        listbox_frame = _tk.Frame(self._frame_files, bg='#1a1a1a')
        listbox_frame.grid(row=0, column=0, padx=12, pady=(12, 8), sticky="nsew")
        listbox_frame.grid_columnconfigure(0, weight=1)
        listbox_frame.grid_rowconfigure(0, weight=1)
        self._file_list_canvas = _tk.Canvas(listbox_frame, bg='#0A0A0A', highlightthickness=0, yscrollincrement=40)
        self._file_list_canvas.grid(row=0, column=0, sticky="nsew")
        self._file_list_inner = _tk.Frame(self._file_list_canvas, bg='#0A0A0A')
        self._file_list_canvas_window = self._file_list_canvas.create_window(0, 0, window=self._file_list_inner, anchor='nw')
        def _on_file_list_configure(event):
            self._file_list_canvas.configure(scrollregion=self._file_list_canvas.bbox('all'))
            self._file_list_canvas.itemconfig(self._file_list_canvas_window, width=event.width)
        self._file_list_inner.bind('<Configure>', _on_file_list_configure)
        self._file_list_canvas.bind('<Configure>', lambda e: self._file_list_canvas.itemconfig(self._file_list_canvas_window, width=e.width))
        def _file_list_wheel(event):
            if getattr(event, 'num', None) == 4:
                self._file_list_canvas.yview_scroll(-3, 'units')
            elif getattr(event, 'num', None) == 5:
                self._file_list_canvas.yview_scroll(3, 'units')
            else:
                delta = getattr(event, 'delta', 0)
                units = max(1, abs(delta) // 40) * (-1 if delta > 0 else 1)
                self._file_list_canvas.yview_scroll(units, 'units')
        # Store so _rebuild_autobe_file_list can propagate to every row/label
        self._file_list_wheel_handler = _file_list_wheel
        for _ev in ('<MouseWheel>', '<Button-4>', '<Button-5>'):
            self._file_list_canvas.bind(_ev, _file_list_wheel)
            self._file_list_inner.bind(_ev, _file_list_wheel)

        # File count label + Select All button row
        _count_row = _tk.Frame(self._frame_files, bg='#1a1a1a')
        _count_row.grid(row=1, column=0, padx=12, pady=(0, 4), sticky="ew")
        _count_row.grid_columnconfigure(0, weight=1)
        self._file_count_label = _tk.Label(_count_row, text=_f("app.files_selected", n=0), bg='#1a1a1a', fg='#FFFFFF', font=("Segoe UI", 10))
        self._file_count_label.grid(row=0, column=0, sticky="w")
        self._btn_select_all = _tk.Button(_count_row, text="Select All", command=self._toggle_select_all_files,
            bg='#2d2d2d', fg='#CCCCCC', font=("Segoe UI", 9), relief='flat', cursor='hand2',
            activebackground='#3d3d3d', activeforeground='#FFFFFF', padx=10, pady=2)
        self._btn_select_all.grid(row=0, column=1, sticky="e")
        self._btn_select_all.grid_remove()  # hidden until files are added

        self._btn_add = _tk.Button(self._frame_files, text="➕ " + _("app.add_files"), command=self._add_files, bg='#9333ea', fg='#FFFFFF', font=("Segoe UI", 11, "bold"), relief='flat', cursor='hand2', activebackground='#a855f7')
        self._btn_add.grid(row=2, column=0, padx=12, pady=(0, 8), sticky="ew")

        self._btn_remove = _tk.Button(self._frame_files, text="🗑️ " + _("app.remove_selected"), command=self._remove_files, bg='#1a1a1a', fg='#FFFFFF', font=("Segoe UI", 11), relief='flat', cursor='hand2', activebackground='#2d2d2d')
        self._btn_remove.grid(row=3, column=0, padx=12, pady=(0, 12), sticky="ew")

        # Configure resizing for file frame
        self._frame_files.grid_columnconfigure(0, weight=1)
        self._frame_files.grid_rowconfigure(0, weight=1)  # Listbox frame - expandable
        self._frame_files.grid_rowconfigure(1, weight=0)  # File count row - fixed
        self._frame_files.grid_rowconfigure(2, weight=0)  # Add button - fixed
        self._frame_files.grid_rowconfigure(3, weight=0)  # Remove button - fixed

        self._frame_output = _tk.LabelFrame(self.app1_frame, text="📂 " + _("app.select_output_dir"), bg='#1a1a1a', fg='#FFFFFF', font=("Segoe UI", 13, "bold"))
        self._frame_output.grid(row=1, column=0, padx=15, pady=15, sticky="nsew")

        self._output_dir_var = _tk.StringVar()
        self._entry_output_dir = _tk.Entry(self._frame_output, textvariable=self._output_dir_var, width=50, bg='#0A0A0A', fg='#FFFFFF', font=("Segoe UI", 11), insertbackground='#a855f7', relief='flat', highlightthickness=1, highlightbackground='#1a1a1a', highlightcolor='#9333ea')
        self._entry_output_dir.grid(row=0, column=0, padx=12, pady=12, sticky="ew", ipady=8)

        self._btn_select_output = _tk.Button(self._frame_output, text=_("app.browse"), command=self._select_output_dir, bg='#9333ea', fg='#FFFFFF', font=("Segoe UI", 11, "bold"), relief='flat', cursor='hand2', activebackground='#a855f7')
        self._btn_select_output.grid(row=0, column=1, padx=(0, 12), pady=12, sticky="ew")

        # Configure resizing for output frame
        self._frame_output.grid_columnconfigure(0, weight=1)

        # Auto-Import vars kept as self attributes so the merge code can read them
        _ai_s = self._load_settings()
        self._auto_import_var = _tk.BooleanVar(value=_ai_s.get("auto_import", False))
        self._mc_path_var = _tk.StringVar(value=_ai_s.get("mc_path", "") or self._detect_com_mojang())
        self._auto_import_var.trace_add('write', lambda *a: self._save_settings())
        self._mc_path_var.trace_add('write', lambda *a: self._save_settings())

        self._frame_buttons = _tk.Frame(self.app1_frame, bg='#000000')
        self._frame_buttons.grid(row=2, column=0, padx=15, pady=15, sticky="ew")

        self._btn_start = _tk.Button(self._frame_buttons, text="🚀 " + _("app.start_process"), command=self._process_and_create_manifest, bg='#9333ea', fg='#FFFFFF', font=("Segoe UI", 12, "bold"), relief='flat', cursor='hand2', activebackground='#a855f7', padx=20, pady=10)
        self._btn_start.grid(row=0, column=0, padx=(0, 8), pady=0, sticky="ew")

        self._btn_check = _tk.Button(self._frame_buttons, text="🔍 " + _("app.check_packs"), command=self._extract_and_show_codes, bg='#9333ea', fg='#FFFFFF', font=("Segoe UI", 12, "bold"), relief='flat', cursor='hand2', activebackground='#a855f7', padx=20, pady=10)
        self._btn_check.grid(row=0, column=1, padx=(8, 4), pady=0, sticky="ew")

        # Excel organization button
        self._btn_excel = _tk.Button(self._frame_buttons, text="📊 Excel", command=self._show_excel_manager, bg='#10b981', fg='#FFFFFF', font=("Segoe UI", 12, "bold"), relief='flat', cursor='hand2', activebackground='#059669', padx=20, pady=10)
        self._btn_excel.grid(row=0, column=2, padx=(4, 4), pady=0, sticky="ew")

        # Achievement Status Button (click opens in-app achievement screen)
        self._btn_achievement_status = _tk.Button(self._frame_buttons, text="✅ " + _("app.achievements_active"), command=self._show_achievement_overlay, bg='#10b981', fg='#FFFFFF', font=("Segoe UI", 11, "bold"), relief='flat', cursor='hand2', activebackground='#059669', padx=15, pady=10)
        self._btn_achievement_status.grid(row=0, column=3, padx=(4, 0), pady=0, sticky="ew")
        
        # Store achievement-disabling packs for overlay screen
        self._achievement_disabling_packs = []
        
        # Initialize achievement status
        self._check_achievement_compatibility()

        # Configure resizing for buttons frame
        self._frame_buttons.grid_columnconfigure(0, weight=1)
        self._frame_buttons.grid_columnconfigure(1, weight=1)
        self._frame_buttons.grid_columnconfigure(2, weight=1)
        self._frame_buttons.grid_columnconfigure(3, weight=0)  # Achievement button - fixed width

        # Progress Display Section - Game-style loading screen
        self._frame_progress = _tk.LabelFrame(self.app1_frame, text="📊 " + _("app.processing_progress"), bg='#1a1a1a', fg='#FFFFFF', font=("Segoe UI", 13, "bold"))
        self._frame_progress.grid(row=3, column=0, padx=15, pady=15, sticky="nsew")
        self._frame_progress.columnconfigure(0, weight=1)
        self._frame_progress.grid_rowconfigure(0, weight=0)  # Progress container - fixed height
        
        progress_container = _tk.Frame(self._frame_progress, bg='#1a1a1a')
        progress_container.grid(row=0, column=0, padx=12, pady=12, sticky="nsew")
        progress_container.columnconfigure(0, weight=1)
        progress_container.rowconfigure(0, weight=0)  # Step label - fixed
        progress_container.rowconfigure(1, weight=0)  # Progress bar - fixed
        progress_container.rowconfigure(2, weight=0)  # Steps frame - fixed
        
        # Current step label
        self._progress_step_label = _tk.Label(progress_container, text=_("app.ready_to_process"), 
                                             bg='#1a1a1a', fg='#FFFFFF', 
                                             font=('Segoe UI', 12, 'bold'),
                                             anchor='w')
        self._progress_step_label.grid(row=0, column=0, sticky="w", pady=(0, 8))
        
        # Progress bar
        style = _ttk.Style()
        style.theme_use('clam')
        style.configure("Progress.Horizontal.TProgressbar", background='#9333ea', troughcolor='#0A0A0A', borderwidth=0)
        self._progress = _ttk.Progressbar(progress_container, orient='horizontal', 
                                         length=400, mode='determinate', 
                                         style="Progress.Horizontal.TProgressbar",
                                         maximum=100)
        self._progress.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        
        # Steps indicator (4 steps)
        steps_frame = _tk.Frame(progress_container, bg='#1a1a1a')
        steps_frame.grid(row=2, column=0, sticky="ew")
        
        self._step_labels = []
        step_names = [_("progress.creating_manifest"), _("progress.processing_files"), _("progress.updating_packs"), _("progress.finalizing")]
        for i, step_name in enumerate(step_names):
            step_frame = _tk.Frame(steps_frame, bg='#1a1a1a')
            step_frame.grid(row=0, column=i, padx=5, sticky="w")
            
            # Step number/status indicator
            step_status = _tk.Label(step_frame, text="○", bg='#1a1a1a', fg='#666666',
                                   font=('Segoe UI', 14), width=3, anchor='w')
            step_status.pack(side='left')
            self._step_labels.append({'status': step_status, 'name': step_name})
            
            # Step name
            step_label = _tk.Label(step_frame, text=step_name, bg='#1a1a1a', fg='#999999',
                                  font=('Segoe UI', 9))
            step_label.pack(side='left')
            self._step_labels[i]['label'] = step_label
        
        self._trademark_label = _tk.Label(self.app1_frame, text=_("app.codenex"), bg='#000000', fg='#FFFFFF', font=("Segoe UI", 10))
        self._trademark_label.grid(row=4, column=0, padx=15, pady=10, sticky="e")
        
        # Update app1_frame row configuration
        self.app1_frame.grid_rowconfigure(4, weight=0)  # Trademark - fixed

    def _create_tooltip(self, widget, text):
        """Create a tooltip for a widget."""
        def on_enter(event):
            # Don't show tooltip if widget is being destroyed
            try:
                if not widget.winfo_exists():
                    return
            except:
                return
            
            # Clean up any existing tooltip first
            if hasattr(widget, 'tooltip'):
                try:
                    if widget.tooltip.winfo_exists():
                        widget.tooltip.destroy()
                except:
                    pass
                try:
                    delattr(widget, 'tooltip')
                except:
                    pass
            
            tooltip = _tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.configure(bg='#1a1a1a', highlightthickness=1, highlightbackground='#9333ea')
            tooltip.attributes('-topmost', True)
            # Wrap long text so tooltip stays on screen; max width ~320px
            wrap = 320
            label = _tk.Label(tooltip, text=text, bg='#1a1a1a', fg='#FFFFFF', font=("Segoe UI", 9), padx=8, pady=4, justify='left', wraplength=wrap)
            label.pack()
            tooltip.update_idletasks()
            w = tooltip.winfo_reqwidth()
            h = tooltip.winfo_reqheight()
            margin = 16
            try:
                sw = self._root.winfo_screenwidth()
                sh = self._root.winfo_screenheight()
            except Exception:
                sw, sh = 800, 600
            x = widget.winfo_rootx() + 20
            y = widget.winfo_rooty() + 20
            if x + w + margin > sw:
                x = sw - w - margin
            if x < margin:
                x = margin
            if y + h + margin > sh:
                y = sh - h - margin
            if y < margin:
                y = margin
            tooltip.geometry(f"+{x}+{y}")
            widget.tooltip = tooltip
        
        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                try:
                    if widget.tooltip.winfo_exists():
                        widget.tooltip.destroy()
                except:
                    pass
                try:
                    delattr(widget, 'tooltip')
                except:
                    pass
        
        def on_destroy(event):
            """Clean up tooltip when widget is destroyed."""
            if hasattr(widget, 'tooltip'):
                try:
                    if widget.tooltip.winfo_exists():
                        widget.tooltip.destroy()
                except:
                    pass
                try:
                    delattr(widget, 'tooltip')
                except:
                    pass
        
        widget.bind('<Enter>', on_enter)
        widget.bind('<Leave>', on_leave)
        widget.bind('<Destroy>', on_destroy)
    
    def init_settings_tab(self):
        """Initialize Settings tab - empty frame, dropdown shown on click."""
        # Empty frame - we'll show dropdown when tab is clicked
        self.settings_frame.configure(bg='#000000')
    
    def _close_settings_dropdown(self):
        """Close settings dropdown and clean up all tooltips."""
        try:
            if hasattr(self, '_settings_dropdown'):
                try:
                    if self._settings_dropdown.winfo_exists():
                        # Clean up all tooltips recursively
                        def cleanup_tooltips(widget):
                            """Recursively clean up tooltips."""
                            try:
                                if hasattr(widget, 'tooltip'):
                                    try:
                                        if widget.tooltip.winfo_exists():
                                            widget.tooltip.destroy()
                                    except:
                                        pass
                                    try:
                                        delattr(widget, 'tooltip')
                                    except:
                                        pass
                                for child in widget.winfo_children():
                                    cleanup_tooltips(child)
                            except:
                                pass
                        
                        if getattr(self, "_settings_marquee_after_id", None) is not None:
                            try:
                                self._root.after_cancel(self._settings_marquee_after_id)
                            except Exception:
                                pass
                            self._settings_marquee_after_id = None
                        cleanup_tooltips(self._settings_dropdown)
                        self._settings_dropdown.destroy()
                except:
                    pass
                try:
                    delattr(self, '_settings_dropdown')
                except:
                    pass
                try:
                    if hasattr(self, '_settings_vol_value_label'):
                        delattr(self, '_settings_vol_value_label')
                except:
                    pass
                try:
                    if hasattr(self, '_settings_refresh_now_playing'):
                        delattr(self, '_settings_refresh_now_playing')
                except:
                    pass
                
                # Unbind click handler
                try:
                    self._root.unbind('<Button-1>')
                except:
                    pass
        except Exception as e:
            log_error(f"Error closing settings dropdown: {e}")
    
    def _on_notebook_click(self, event):
        """Intercept notebook clicks to prevent Settings tab from switching."""
        try:
            # Find which tab was clicked
            x, y = event.x, event.y
            clicked_tab = self.notebook.index(f"@{x},{y}")
            
            # Find Settings tab index
            total_tabs = self.notebook.index("end")
            settings_index = None
            for i in range(total_tabs):
                try:
                    if self.notebook.tab(i, "text") == _("tabs.settings"):
                        settings_index = i
                        break
                except:
                    continue
            
            # If Settings tab was clicked, prevent tab change and show dropdown
            if settings_index is not None and clicked_tab == settings_index:
                # Store current tab before it changes
                current_tab = self.notebook.index(self.notebook.select())
                if current_tab != settings_index:
                    if not hasattr(self, '_last_tab_index'):
                        self._last_tab_index = current_tab
                    # Prevent tab change by switching back after event
                    self._root.after_idle(lambda: self.notebook.select(self._last_tab_index))
                
                # Show dropdown
                self._root.after(10, self._show_settings_dropdown)
                return "break"  # Prevent default tab change
        except Exception as e:
            # If we can't determine which tab, let it proceed normally
            pass
    
    def _on_settings_tab_click(self, event=None):
        """Legacy handler - no longer used but kept for compatibility."""
        pass
    
    def _show_settings_dropdown(self):
        """Show settings dropdown menu."""
        try:
            # Close existing dropdown if open
            self._close_settings_dropdown()
            
            # Get notebook and app window positions
            self.notebook.update_idletasks()
            self._root.update_idletasks()
            
            notebook_x = self.notebook.winfo_rootx()
            notebook_y = self.notebook.winfo_rooty()
            notebook_width = self.notebook.winfo_width()
            
            app_x = self._root.winfo_rootx()
            app_y = self._root.winfo_rooty()
            app_width = self._root.winfo_width()
            app_height = self._root.winfo_height()
            
            # Find Settings tab position dynamically
            total_tabs = self.notebook.index("end")
            settings_tab_index = None
            for i in range(total_tabs):
                if self.notebook.tab(i, "text") == _("tabs.settings"):
                    settings_tab_index = i
                    break
            
            if settings_tab_index is None:
                settings_tab_index = 4  # Fallback
            
            # Approximate tab width (notebook width / number of tabs)
            tab_width = notebook_width / total_tabs if total_tabs > 0 else 100
            tab_x = notebook_x + (settings_tab_index * tab_width) + (tab_width / 2)
            tab_y = notebook_y + 35  # Below tab bar
            
            # Create dropdown menu (Toplevel - proper menu panel)
            self._settings_dropdown = _tk.Toplevel(self._root)
            self._settings_dropdown.wm_overrideredirect(True)
            self._settings_dropdown.configure(bg='#9333ea')  # Border color
            
            # Fit dropdown to window: width within app, height within app
            menu_width = min(400, max(320, app_width - 80))
            menu_height = min(520, max(380, app_height - 80))
            
            dropdown_x = int(tab_x - menu_width // 2)
            dropdown_y = int(tab_y)
            if dropdown_x < app_x:
                dropdown_x = app_x + 10
            if dropdown_x + menu_width > app_x + app_width:
                dropdown_x = app_x + app_width - menu_width - 10
            if dropdown_y + menu_height > app_y + app_height:
                dropdown_y = app_y + app_height - menu_height - 10
            
            self._settings_dropdown.geometry(f"{menu_width}x{menu_height}+{dropdown_x}+{dropdown_y}")
            self._settings_dropdown.attributes('-topmost', False)
            self._settings_dropdown.transient(self._root)
            try:
                self._settings_dropdown.deiconify()
            except:
                pass
            self._settings_dropdown.lift(self._root)
            self._settings_dropdown.update_idletasks()
            
            # Inner: panel with scrollable content (hover + mouse wheel to scroll)
            inner = _tk.Frame(self._settings_dropdown, bg='#252525', highlightthickness=0)
            inner.place(x=2, y=2, width=menu_width-4, height=menu_height-4)
            inner.grid_rowconfigure(1, weight=1)
            inner.grid_columnconfigure(0, weight=1)

            # ── Header row: title + close button ────────────────────────────
            _hdr = _tk.Frame(inner, bg='#1e1e1e', height=26)
            _hdr.grid(row=0, column=0, sticky='ew')
            _hdr.grid_propagate(False)
            _tk.Label(_hdr, text="⚙  Settings",
                      bg='#1e1e1e', fg='#aaaaaa',
                      font=("Segoe UI", 9)).place(x=10, rely=0.5, anchor='w')
            _tk.Button(
                _hdr, text='✕',
                bg='#1e1e1e', fg='#666666',
                font=("Segoe UI", 9, "bold"),
                relief='flat', cursor='hand2',
                activebackground='#7f1d1d', activeforeground='#FFFFFF',
                padx=6, pady=0,
                command=self._close_settings_dropdown
            ).place(relx=1.0, rely=0.5, anchor='e')

            canvas = _tk.Canvas(inner, bg='#252525', highlightthickness=0)
            canvas.grid(row=1, column=0, sticky='nsew')
            content_outer = _tk.Frame(canvas, bg='#252525')
            content = _tk.Frame(content_outer, bg='#252525')
            content.pack(fill='both', expand=True, padx=16, pady=16)
            canvas_window = canvas.create_window(0, 0, window=content_outer, anchor='nw')
            def _on_content_configure(event):
                canvas.configure(scrollregion=canvas.bbox('all'))
            content_outer.bind('<Configure>', _on_content_configure)
            def _on_canvas_configure(event):
                canvas.itemconfig(canvas_window, width=event.width)
            canvas.bind('<Configure>', _on_canvas_configure)
            def _on_mousewheel(event):
                if self._settings_dropdown.winfo_exists():
                    canvas.yview_scroll(int(-1 * (event.delta / 120)), 'units')
            def _scroll_bind_enter(event):
                canvas.bind_all('<MouseWheel>', _on_mousewheel)
            def _scroll_bind_leave(event):
                try:
                    canvas.unbind_all('<MouseWheel>')
                except Exception:
                    pass
            canvas.bind('<Enter>', _scroll_bind_enter)
            canvas.bind('<Leave>', _scroll_bind_leave)
            
            # ---- Section 1: App language (stacked vertically so all are visible and clickable) ----
            lang_label = _tk.Label(content, text=_("settings.app_language"), bg='#252525', fg='#E5E7EB',
                                  font=("Segoe UI", 11, "bold"))
            lang_label.pack(anchor='w', pady=(0, 8))
            lang_btn_frame = _tk.Frame(content, bg='#252525')
            lang_btn_frame.pack(fill='x', pady=(0, 14))
            def set_lang(lang):
                self._current_lang = lang
                self._save_settings()
                _tr_load(lang)
                self._close_settings_dropdown()
                self._show_themed_info_dialog(_("update.title"), _("settings.language_saved"))
            for code, label_key in [("en", "lang.english"), ("es", "lang.spanish"), ("zh", "lang.chinese"), ("id", "lang.indonesian"), ("ru", "lang.russian"), ("pt", "lang.portuguese_br")]:
                b = _tk.Button(lang_btn_frame, text=_(label_key), command=lambda c=code: set_lang(c),
                              bg='#3a3a3a', fg='#FFFFFF', font=("Segoe UI", 10), relief='flat', cursor='hand2',
                              activebackground='#9333ea', activeforeground='#FFFFFF', padx=14, pady=8, anchor='w')
                b.pack(fill='x', pady=(0, 4))
            
            _tk.Frame(content, bg='#404040', height=2).pack(fill='x', pady=(0, 12))
            
            # ---- Section 2: MCPACKER mode ----
            setting_label = _tk.Label(content, text=_("settings.mcpacker_mode"), bg='#252525', fg='#E5E7EB',
                                      font=("Segoe UI", 11, "bold"))
            setting_label.pack(anchor='w', pady=(0, 8))
            self._create_tooltip(setting_label, "Choose how MCPACKER processes files:\n• Pack: Converts folders to .mcpack files\n• Extract: Unzips .mcpack/.mcaddon/.zip files to folders")
            
            mode_frame = _tk.Frame(content, bg='#252525')
            mode_frame.pack(fill='x', pady=(0, 14))
            current_mode = self.mcpacker_mode_var.get()
            def close_dropdown_and_set_mode(mode):
                self._set_mcpacker_mode(mode)
                self._close_settings_dropdown()
            
            pack_container = _tk.Frame(mode_frame, bg='#252525')
            pack_container.pack(fill='x', pady=(0, 6))
            pack_check = _tk.Label(pack_container, text="✓" if current_mode == "pack" else "○", bg='#252525',
                                  fg='#9333ea' if current_mode == "pack" else '#666666', font=("Segoe UI", 12), width=2)
            pack_check.pack(side='left', padx=(0, 10))
            pack_btn = _tk.Button(pack_container, text=_("settings.pack"), command=lambda: close_dropdown_and_set_mode("pack"),
                                 bg='#3a3a3a', fg='#FFFFFF', font=("Segoe UI", 10, "bold" if current_mode == "pack" else "normal"),
                                 relief='flat', cursor='hand2', activebackground='#9333ea', activeforeground='#FFFFFF',
                                 padx=14, pady=8, anchor='w')
            pack_btn.pack(side='left', fill='x', expand=True)
            self._create_tooltip(pack_btn, "Converts folder structures into .mcpack files")
            
            extract_container = _tk.Frame(mode_frame, bg='#252525')
            extract_container.pack(fill='x')
            extract_check = _tk.Label(extract_container, text="✓" if current_mode == "extract" else "○", bg='#252525',
                                      fg='#9333ea' if current_mode == "extract" else '#666666', font=("Segoe UI", 12), width=2)
            extract_check.pack(side='left', padx=(0, 10))
            extract_btn = _tk.Button(extract_container, text=_("settings.extract"), command=lambda: close_dropdown_and_set_mode("extract"),
                                    bg='#3a3a3a', fg='#FFFFFF', font=("Segoe UI", 10, "bold" if current_mode == "extract" else "normal"),
                                    relief='flat', cursor='hand2', activebackground='#9333ea', activeforeground='#FFFFFF',
                                    padx=14, pady=8, anchor='w')
            extract_btn.pack(side='left', fill='x', expand=True)
            self._create_tooltip(extract_btn, "Unzips .mcpack/.mcaddon/.zip files into folder structures")
            
            if current_mode == "pack":
                pack_btn.config(bg='#9333ea', fg='#FFFFFF')
            else:
                extract_btn.config(bg='#9333ea', fg='#FFFFFF')
            
            _tk.Frame(content, bg='#404040', height=2).pack(fill='x', pady=(0, 12))
            
            # ---- Section 2b: Merge by script version (AutoBE tab) ----
            content_width = menu_width - 4 - 32
            merge_by_ver_label = _tk.Label(content, text=_("settings.merge_by_version"), bg='#252525', fg='#E5E7EB',
                                           font=("Segoe UI", 11, "bold"), wraplength=content_width, justify='left')
            merge_by_ver_label.pack(anchor='w', pady=(0, 8))
            self._create_tooltip(merge_by_ver_label, _("settings.merge_by_version_tooltip"))
            merge_by_ver_cb = _tk.Checkbutton(content, text=_("settings.merge_by_version_check"),
                                              variable=self.merge_by_version_var, bg='#252525', fg='#FFFFFF',
                                              selectcolor='#1a1a1a', activebackground='#252525', activeforeground='#FFFFFF',
                                              font=("Segoe UI", 10), relief='flat', cursor='hand2',
                                              wraplength=content_width, justify='left')
            merge_by_ver_cb.pack(anchor='w', pady=(0, 14))
            
            _tk.Frame(content, bg='#404040', height=2).pack(fill='x', pady=(0, 12))
            
            # ---- Section 2c: Customize merged pack after merge ----
            content_width_custom = menu_width - 4 - 32
            custom_label = _tk.Label(content, text=_("settings.customize_pack_after_merge") if _("settings.customize_pack_after_merge") != "settings.customize_pack_after_merge" else "Name merged pack after merge", bg='#252525', fg='#E5E7EB', font=("Segoe UI", 11, "bold"), wraplength=content_width_custom, justify='left')
            custom_label.pack(anchor='w', pady=(0, 8))
            self._create_tooltip(custom_label, _("settings.customize_pack_after_merge_tooltip") if _("settings.customize_pack_after_merge_tooltip") != "settings.customize_pack_after_merge_tooltip" else "After merge completes, prompt to set pack name, description, and icon.")
            custom_cb = _tk.Checkbutton(content, text=_("settings.customize_pack_after_merge_check") if _("settings.customize_pack_after_merge_check") != "settings.customize_pack_after_merge_check" else "Prompt to name pack and pick icon after merge",
                                        variable=self.customize_pack_after_merge_var, bg='#252525', fg='#FFFFFF',
                                        selectcolor='#1a1a1a', activebackground='#252525', activeforeground='#FFFFFF',
                                        font=("Segoe UI", 10), relief='flat', cursor='hand2',
                                        wraplength=content_width_custom, justify='left')
            custom_cb.pack(anchor='w', pady=(0, 14))
            
            _tk.Frame(content, bg='#404040', height=2).pack(fill='x', pady=(0, 12))
            
            # ---- Section 2d: Show linked packs after merge ----
            linked_label = _tk.Label(content, text=_("settings.show_linked_packs_after_merge") if _("settings.show_linked_packs_after_merge") != "settings.show_linked_packs_after_merge" else "Show linked packs after merge", bg='#252525', fg='#E5E7EB', font=("Segoe UI", 11, "bold"), wraplength=content_width_custom, justify='left')
            linked_label.pack(anchor='w', pady=(0, 8))
            self._create_tooltip(linked_label, _("settings.show_linked_packs_after_merge_tooltip") if _("settings.show_linked_packs_after_merge_tooltip") != "settings.show_linked_packs_after_merge_tooltip" else "After merge, show the list of addons in this merge so you can view or remove one.")
            linked_cb = _tk.Checkbutton(content, text=_("settings.show_linked_packs_after_merge_check") if _("settings.show_linked_packs_after_merge_check") != "settings.show_linked_packs_after_merge_check" else "Show linked packs list after merge",
                                        variable=self.show_linked_packs_after_merge_var, bg='#252525', fg='#FFFFFF',
                                        selectcolor='#1a1a1a', activebackground='#252525', activeforeground='#FFFFFF',
                                        font=("Segoe UI", 10), relief='flat', cursor='hand2',
                                        wraplength=content_width_custom, justify='left')
            linked_cb.pack(anchor='w', pady=(0, 14))

            _tk.Frame(content, bg='#404040', height=2).pack(fill='x', pady=(0, 12))

            # ---- Section 2e: ExtendedBE addon fixer ----
            _ebe_fixer_count = len(_EXTENDEDBE_FIXERS)
            _ebe_tooltip = (
                f"Repairs known bugs and outdated code in addons before merging.\n"
                f"Fixes things like misplaced files, broken events, missing definitions,\n"
                f"and outdated sound entries — without modifying the original .mcpack.\n\n"
                f"{_ebe_fixer_count} fixer{'s' if _ebe_fixer_count != 1 else ''} currently loaded  |  AutoBE/extendedbe/"
            )
            _ebe_label = _tk.Label(content,
                                   text="Addon Fixer",
                                   bg='#252525', fg='#E5E7EB',
                                   font=("Segoe UI", 11, "bold"),
                                   wraplength=content_width_custom, justify='left')
            _ebe_label.pack(anchor='w', pady=(0, 2))
            _tk.Label(content,
                      text="Auto-repairs broken or outdated addons before merging",
                      bg='#252525', fg='#6b7280',
                      font=("Segoe UI", 9),
                      wraplength=content_width_custom, justify='left').pack(anchor='w', pady=(0, 8))
            self._create_tooltip(_ebe_label, _ebe_tooltip)
            _ebe_cb = _tk.Checkbutton(content,
                                      text="Enable addon fixer",
                                      variable=self.extendedbe_enabled_var,
                                      bg='#252525', fg='#FFFFFF',
                                      selectcolor='#1a1a1a',
                                      activebackground='#252525', activeforeground='#FFFFFF',
                                      font=("Segoe UI", 10), relief='flat', cursor='hand2',
                                      wraplength=content_width_custom, justify='left')
            self._create_tooltip(_ebe_cb, _ebe_tooltip)
            _ebe_cb.pack(anchor='w', pady=(0, 14))

            _tk.Frame(content, bg='#404040', height=2).pack(fill='x', pady=(0, 12))

            # ---- Section 2f: Modpack Organization (Excel/CSV) ----
            excel_tooltip = (
                "Automatically organize your addons into Excel/CSV files for better management.\n"
                "Each modpack gets its own sheet with addon details, versions, and compatibility info.\n"
                "Enables easy tracking, sharing, and management of your modpack configurations.\n"
                "Uses CSV format by default (works in Excel without additional dependencies)."
            )
            excel_label = _tk.Label(content,
                                   text="Modpack Organization",
                                   bg='#252525', fg='#E5E7EB',
                                   font=("Segoe UI", 11, "bold"),
                                   wraplength=content_width_custom, justify='left')
            excel_label.pack(anchor='w', pady=(0, 2))
            _tk.Label(content,
                      text="Track addons, versions, and compatibility in Excel/CSV files",
                      bg='#252525', fg='#6b7280',
                      font=("Segoe UI", 9),
                      wraplength=content_width_custom, justify='left').pack(anchor='w', pady=(0, 8))
            self._create_tooltip(excel_label, excel_tooltip)
            excel_cb = _tk.Checkbutton(content,
                                      text="Enable Excel/CSV organization",
                                      variable=self.modpack_organization_var,
                                      bg='#252525', fg='#FFFFFF',
                                      selectcolor='#1a1a1a',
                                      activebackground='#252525', activeforeground='#FFFFFF',
                                      font=("Segoe UI", 10), relief='flat', cursor='hand2',
                                      wraplength=content_width_custom, justify='left')
            self._create_tooltip(excel_cb, excel_tooltip)
            excel_cb.pack(anchor='w', pady=(0, 14))


            _tk.Frame(content, bg='#404040', height=2).pack(fill='x', pady=(0, 12))

            # ---- Section 2e: Background music ----
            music_label = _tk.Label(content, text="Background music" if _("settings.background_music") == "settings.background_music" else _("settings.background_music"), bg='#252525', fg='#E5E7EB', font=("Segoe UI", 11, "bold"), wraplength=content_width_custom, justify='left')
            music_label.pack(anchor='w', pady=(0, 8))
            self._create_tooltip(music_label, _("settings.background_music_tooltip") if _("settings.background_music_tooltip") != "settings.background_music_tooltip" else "Play non-copyright lofi-style music from the music/ folder (e.g. background.ogg). Requires pygame.")
            music_cb = _tk.Checkbutton(content, text="Play background music" if _("settings.background_music_check") == "settings.background_music_check" else _("settings.background_music_check"),
                                        variable=self.background_music_var, bg='#252525', fg='#FFFFFF',
                                        selectcolor='#1a1a1a', activebackground='#252525', activeforeground='#FFFFFF',
                                        font=("Segoe UI", 10), relief='flat', cursor='hand2',
                                        wraplength=content_width_custom, justify='left')
            music_cb.pack(anchor='w', pady=(0, 8))
            # Playlist selector from music subfolders (music/<playlist-name>/...)
            _playlist_label = _tk.Label(content, text="Playlist", bg='#252525', fg='#E5E7EB', font=("Segoe UI", 10))
            _playlist_label.pack(anchor='w', pady=(0, 4))
            playlist_values = ["__all__"] + self._get_available_music_playlists()
            current_playlist = self._sanitize_playlist_key(
                getattr(self, "music_playlist_var", _tk.StringVar(value="__all__")).get()
            )
            if current_playlist not in playlist_values:
                current_playlist = "__all__"
            _playlist_labels = [("All music" if p == "__all__" else p) for p in playlist_values]
            _playlist_label_to_value = {
                ("All music" if p == "__all__" else p): p for p in playlist_values
            }
            _playlist_ui_var = _tk.StringVar(
                value=("All music" if current_playlist == "__all__" else current_playlist)
            )
            playlist_combo = _ttk.Combobox(
                content,
                textvariable=_playlist_ui_var,
                values=_playlist_labels,
                state="readonly",
                width=36,
            )
            playlist_combo.pack(anchor='w', pady=(0, 8), fill='x')
            def _on_playlist_pick(event=None):
                try:
                    picked_label = _playlist_ui_var.get()
                    picked_value = _playlist_label_to_value.get(picked_label, "__all__")
                    picked_value = self._sanitize_playlist_key(picked_value)
                    if getattr(self, "music_playlist_var", None) and self.music_playlist_var.get() != picked_value:
                        self.music_playlist_var.set(picked_value)
                except Exception:
                    pass
            playlist_combo.bind("<<ComboboxSelected>>", _on_playlist_pick)
            self._create_tooltip(
                playlist_combo,
                "Choose a music playlist folder from music/. Use 'All music' to play everything."
            )
            music_vol_label = _tk.Label(content, text="Music volume" if _("settings.music_volume") == "settings.music_volume" else _("settings.music_volume"), bg='#252525', fg='#E5E7EB', font=("Segoe UI", 10), wraplength=content_width_custom, justify='left')
            music_vol_label.pack(anchor='w', pady=(0, 4))
            # Use ttk.Scale to avoid hover glitching (tk.Scale redraws/jumps on hover). Custom style is created, not a theme.
            _vol_style_name = "DarkVol.Horizontal.TScale"
            try:
                _s = _ttk.Style()
                _s.configure(_vol_style_name, background='#252525', troughcolor='#404040')
                _s.map(_vol_style_name, background=[('active', '#9333ea')])
            except Exception:
                pass
            try:
                music_vol_scale = _ttk.Scale(content, from_=0, to=100, orient=_tk.HORIZONTAL, variable=self.background_music_volume_var, length=200, style=_vol_style_name)
            except Exception:
                music_vol_scale = _tk.Scale(content, from_=0, to=100, orient=_tk.HORIZONTAL, variable=self.background_music_volume_var, bg='#252525', fg='#E5E7EB', troughcolor='#404040', highlightthickness=0, activebackground='#252525', length=200, showvalue=False, resolution=5, takefocus=0, sliderrelief='flat', bd=0)
            music_vol_scale.pack(anchor='w', pady=(0, 4))
            _vol_value_label = _tk.Label(content, text=str(getattr(self, "background_music_volume_var", _tk.IntVar(value=70)).get()) + "%", bg='#252525', fg='#E5E7EB', font=("Segoe UI", 9))
            _vol_value_label.pack(anchor='w', pady=(0, 2))
            self._settings_vol_value_label = _vol_value_label  # updated by existing volume trace when dropdown open
            # Music transport controls (Apple Music style): shuffle / previous / next
            controls_frame = _tk.Frame(content, bg='#252525')
            controls_frame.pack(fill='x', pady=(0, 8))
            shuffle_cb = _tk.Checkbutton(
                controls_frame,
                text="Shuffle",
                variable=self.music_shuffle_var,
                bg='#252525',
                fg='#FFFFFF',
                selectcolor='#1a1a1a',
                activebackground='#252525',
                activeforeground='#FFFFFF',
                font=("Segoe UI", 10),
                relief='flat',
                cursor='hand2'
            )
            shuffle_cb.pack(side='left')
            transport_frame = _tk.Frame(controls_frame, bg='#252525')
            transport_frame.pack(side='right')
            # Placeholder callback; rebound after now-playing canvas is created.
            _refresh_now_playing_canvas = lambda: None
            prev_btn = _tk.Button(
                transport_frame, text="⏮", command=lambda: (self._play_previous_track(show_popup=True, popup_force=True), _refresh_now_playing_canvas()),
                bg='#3a3a3a', fg='#FFFFFF', font=("Segoe UI", 11), relief='flat', cursor='hand2',
                activebackground='#9333ea', activeforeground='#FFFFFF', padx=10, pady=3
            )
            prev_btn.pack(side='left', padx=(0, 6))
            next_btn = _tk.Button(
                transport_frame, text="⏭", command=lambda: (self._play_next_track(show_popup=True, popup_force=True), _refresh_now_playing_canvas()),
                bg='#3a3a3a', fg='#FFFFFF', font=("Segoe UI", 11), relief='flat', cursor='hand2',
                activebackground='#9333ea', activeforeground='#FFFFFF', padx=10, pady=3
            )
            next_btn.pack(side='left')
            self._create_tooltip(shuffle_cb, "Shuffle playback order.")
            self._create_tooltip(prev_btn, "Play previous song.")
            self._create_tooltip(next_btn, "Play next song.")
            # Now playing (marquee for long names; cleaned title formatting)
            self._settings_marquee_after_id = None
            _np_canvas_w = content_width_custom
            _np_canvas_h = 18
            _np_font = _font.Font(family="Segoe UI", size=9)
            now_playing_canvas = _tk.Canvas(content, width=_np_canvas_w, height=_np_canvas_h, bg="#252525", highlightthickness=0)
            now_playing_canvas.pack(anchor="w", pady=(0, 14))
            def _render_now_playing_canvas():
                try:
                    if getattr(self, "_settings_marquee_after_id", None) is not None:
                        try:
                            self._root.after_cancel(self._settings_marquee_after_id)
                        except Exception:
                            pass
                        self._settings_marquee_after_id = None
                    if not now_playing_canvas.winfo_exists():
                        return
                    now_playing_canvas.delete("all")
                    _now_playing = self._format_track_display_name(getattr(self, "_current_track_name", None))
                    if _now_playing and _now_playing != "Unknown":
                        _np_text = "Now playing: " + _now_playing
                        _np_text_width = _np_font.measure(_np_text)
                        if _np_text_width <= _np_canvas_w - 4:
                            now_playing_canvas.create_text(2, _np_canvas_h // 2, text=_np_text, fill="#9ca3af", font=("Segoe UI", 9), anchor="w")
                        else:
                            _gap = "     "
                            _np_loop_text = _np_text + _gap + _np_text
                            _reset_at = _np_font.measure(_np_text + _gap)
                            _np_tid = now_playing_canvas.create_text(2, _np_canvas_h // 2, text=_np_loop_text, fill="#9ca3af", font=("Segoe UI", 9), anchor="w")
                            _np_x = [2]
                            _NP_MS = 28
                            _NP_STEP = 1
                            def _settings_marquee_step():
                                if not getattr(self, "_settings_dropdown", None) or not self._settings_dropdown.winfo_exists():
                                    return
                                try:
                                    if not now_playing_canvas.winfo_exists():
                                        return
                                    now_playing_canvas.coords(_np_tid, _np_x[0], _np_canvas_h // 2)
                                    _np_x[0] -= _NP_STEP
                                    if _np_x[0] <= -_reset_at:
                                        _np_x[0] = 2
                                    self._settings_marquee_after_id = self._root.after(_NP_MS, _settings_marquee_step)
                                except Exception:
                                    pass
                            self._settings_marquee_after_id = self._root.after(450, _settings_marquee_step)
                            self._create_tooltip(now_playing_canvas, _np_text)
                    else:
                        now_playing_canvas.create_text(_np_canvas_w // 2, _np_canvas_h // 2, text="Nothing playing", fill="#9ca3af", font=("Segoe UI", 9), anchor="center")
                except Exception:
                    pass
            _refresh_now_playing_canvas = _render_now_playing_canvas
            self._settings_refresh_now_playing = _refresh_now_playing_canvas
            _render_now_playing_canvas()
            self._create_tooltip(music_vol_scale, "Background music volume (0-100%). Applied immediately." if _("settings.music_volume_tooltip") == "settings.music_volume_tooltip" else _("settings.music_volume_tooltip"))
            
            _tk.Frame(content, bg='#404040', height=2).pack(fill='x', pady=(0, 12))

            # ---- Section: Auto-Import to Minecraft Bedrock ----
            _ai_cw = menu_width - 4 - 32
            ai_label = _tk.Label(content, text="🎮 Auto-Import to Minecraft Bedrock", bg='#252525', fg='#E5E7EB',
                                 font=("Segoe UI", 11, "bold"), wraplength=_ai_cw, justify='left')
            ai_label.pack(anchor='w', pady=(0, 6))
            self._create_tooltip(ai_label, "After merging, automatically copy the merged packs into Minecraft Bedrock's com.mojang folder.")
            _ai_chk = _tk.Checkbutton(content, text="Auto-import after merge",
                                      variable=self._auto_import_var, bg='#252525', fg='#FFFFFF',
                                      selectcolor='#1a1a1a', activebackground='#252525', activeforeground='#FFFFFF',
                                      font=("Segoe UI", 10), relief='flat', cursor='hand2')
            _ai_chk.pack(anchor='w', pady=(0, 8))
            _ai_path_frame = _tk.Frame(content, bg='#252525')
            _ai_path_frame.pack(fill='x', pady=(0, 4))
            _ai_path_frame.columnconfigure(0, weight=1)
            _ai_enabled = self._auto_import_var.get()
            self._entry_mc_path = _tk.Entry(
                _ai_path_frame, textvariable=self._mc_path_var,
                bg='#1a1a1a', fg='#FFFFFF' if _ai_enabled else '#888888',
                font=("Segoe UI", 9), insertbackground='#a855f7',
                relief='flat', highlightthickness=1, highlightbackground='#3a3a3a',
                highlightcolor='#9333ea', state='normal' if _ai_enabled else 'disabled')
            self._entry_mc_path.grid(row=0, column=0, padx=(0, 6), sticky='ew', ipady=5)
            self._btn_mc_browse = _tk.Button(
                _ai_path_frame, text="Browse", command=self._browse_mc_path,
                bg='#9333ea' if _ai_enabled else '#374151',
                fg='#FFFFFF' if _ai_enabled else '#888888',
                font=("Segoe UI", 9, "bold"), relief='flat', cursor='hand2',
                activebackground='#a855f7', state='normal' if _ai_enabled else 'disabled')
            self._btn_mc_browse.grid(row=0, column=1, sticky='ew')
            _ai_chk.config(command=self._toggle_mc_import_path)

            _tk.Frame(content, bg='#404040', height=2).pack(fill='x', pady=(12, 12))

            # ---- Section 3: Check for updates ----
            update_btn = _tk.Button(content, text=_("settings.check_for_updates"), command=self._check_for_updates,
                                   bg='#3a3a3a', fg='#FFFFFF', font=("Segoe UI", 11), relief='flat', cursor='hand2',
                                   activebackground='#9333ea', activeforeground='#FFFFFF', padx=14, pady=12, anchor='w')
            update_btn.pack(fill='x', pady=(0, 0))
            
            # Close dropdown when clicking outside.
            # Use screen bounding-box test — reliable even inside canvas create_window.
            def close_on_click(event):
                try:
                    if not hasattr(self, "_settings_dropdown") or not self._settings_dropdown.winfo_exists():
                        return
                    # Suppress during file dialogs or other blocking calls
                    if getattr(self, '_suppress_settings_close', False):
                        return
                    # Bounding-box test in screen coordinates
                    try:
                        _dx = self._settings_dropdown.winfo_rootx()
                        _dy = self._settings_dropdown.winfo_rooty()
                        _dw = self._settings_dropdown.winfo_width()
                        _dh = self._settings_dropdown.winfo_height()
                        if _dx <= event.x_root <= _dx + _dw and _dy <= event.y_root <= _dy + _dh:
                            return  # click was inside dropdown area
                    except Exception:
                        pass
                    # Also skip notebook tab bar clicks (re-toggle)
                    try:
                        if event.widget == self.notebook:
                            return
                    except Exception:
                        pass
                    self._close_settings_dropdown()
                except Exception:
                    pass
            
            self._root.bind('<Button-1>', close_on_click, add='+')
            
            # Clean up on dropdown destroy
            def on_dropdown_destroy(event=None):
                self._close_settings_dropdown()
            
            self._settings_dropdown.bind('<Destroy>', on_dropdown_destroy)
        except Exception as e:
            log_error(f"Error showing settings dropdown: {e}")
            import traceback
            log_error(traceback.format_exc())

    def init_mcpacker_tab(self):
        # Configure mcpacker_frame for proper resizing (will be set after all widgets are created)
        
        # LabelFrame for selecting input files - Modern styling
        self._frame_mcpacker_files = _tk.LabelFrame(self.mcpacker_frame, text="📦 " + _("mcpacker.select_files"), bg='#1a1a1a', fg='#FFFFFF', font=("Segoe UI", 13, "bold"))
        self._frame_mcpacker_files.grid(row=0, column=0, padx=15, pady=(15, 10), sticky="nsew")

        self._mcpacker_file_list_data = []
        self._mcpacker_file_list_photo_refs = []
        self._mcpacker_file_list_selected = set()
        self._mcpacker_file_paths = {}
        self._mcpacker_files = []

        listbox_frame = _tk.Frame(self._frame_mcpacker_files, bg='#1a1a1a')
        listbox_frame.grid(row=0, column=0, padx=12, pady=(8, 6), sticky="nsew")
        listbox_frame.grid_columnconfigure(0, weight=1)
        listbox_frame.grid_rowconfigure(0, weight=1)
        self._mcpacker_file_list_canvas = _tk.Canvas(listbox_frame, bg='#0A0A0A', highlightthickness=0, yscrollincrement=40)
        self._mcpacker_file_list_canvas.grid(row=0, column=0, sticky="nsew")
        self._mcpacker_file_list_inner = _tk.Frame(self._mcpacker_file_list_canvas, bg='#0A0A0A')
        self._mcpacker_file_list_canvas_window = self._mcpacker_file_list_canvas.create_window(0, 0, window=self._mcpacker_file_list_inner, anchor='nw')
        def _on_mcpacker_list_configure(event):
            self._mcpacker_file_list_canvas.configure(scrollregion=self._mcpacker_file_list_canvas.bbox('all'))
            self._mcpacker_file_list_canvas.itemconfig(self._mcpacker_file_list_canvas_window, width=event.width)
        self._mcpacker_file_list_inner.bind('<Configure>', _on_mcpacker_list_configure)
        self._mcpacker_file_list_canvas.bind('<Configure>', lambda e: self._mcpacker_file_list_canvas.itemconfig(self._mcpacker_file_list_canvas_window, width=e.width))
        def _mcpacker_wheel(e):
            if getattr(e, 'num', None) == 4:
                self._mcpacker_file_list_canvas.yview_scroll(-3, 'units')
            elif getattr(e, 'num', None) == 5:
                self._mcpacker_file_list_canvas.yview_scroll(3, 'units')
            else:
                delta = getattr(e, 'delta', 0)
                units = max(1, abs(delta) // 40) * (-1 if delta > 0 else 1)
                self._mcpacker_file_list_canvas.yview_scroll(units, 'units')
        # Store so _rebuild_mcpacker_file_list can propagate to every row/label
        self._mcpacker_wheel_handler = _mcpacker_wheel
        for _ev in ('<MouseWheel>', '<Button-4>', '<Button-5>'):
            self._mcpacker_file_list_canvas.bind(_ev, _mcpacker_wheel)
            self._mcpacker_file_list_inner.bind(_ev, _mcpacker_wheel)

        # File count label + Select All button row
        _mp_count_row = _tk.Frame(self._frame_mcpacker_files, bg='#1a1a1a')
        _mp_count_row.grid(row=1, column=0, padx=12, pady=(0, 6), sticky="ew")
        _mp_count_row.grid_columnconfigure(0, weight=1)
        self._mcpacker_file_count_label = _tk.Label(_mp_count_row, text=_f("app.files_selected", n=0), bg='#1a1a1a', fg='#FFFFFF', font=("Segoe UI", 10))
        self._mcpacker_file_count_label.grid(row=0, column=0, sticky="w")
        self._mcpacker_btn_select_all = _tk.Button(_mp_count_row, text="Select All", command=self._toggle_select_all_mcpacker,
            bg='#2d2d2d', fg='#CCCCCC', font=("Segoe UI", 9), relief='flat', cursor='hand2',
            activebackground='#3d3d3d', activeforeground='#FFFFFF', padx=10, pady=2)
        self._mcpacker_btn_select_all.grid(row=0, column=1, sticky="e")
        self._mcpacker_btn_select_all.grid_remove()  # hidden until files are added

        # Button container for better alignment
        button_container = _tk.Frame(self._frame_mcpacker_files, bg='#1a1a1a')
        button_container.grid(row=2, column=0, padx=12, pady=(0, 8), sticky="ew")
        button_container.grid_columnconfigure(0, weight=1)
        button_container.grid_columnconfigure(1, weight=1)
        
        # Browse Button for selecting files - Modern styling
        self._btn_mcpacker_browse_files = _tk.Button(button_container, text="➕ " + _("app.add_files"), command=self.select_files, bg='#9333ea', fg='#FFFFFF', font=("Segoe UI", 11, "bold"), relief='flat', cursor='hand2', activebackground='#a855f7')
        self._btn_mcpacker_browse_files.grid(row=0, column=0, padx=(0, 6), sticky="ew")
        
        # Remove Selected Button - Modern styling
        self._btn_mcpacker_remove = _tk.Button(button_container, text="🗑️ " + _("app.remove_selected"), command=self.remove_mcpacker_files, bg='#1a1a1a', fg='#FFFFFF', font=("Segoe UI", 11), relief='flat', cursor='hand2', activebackground='#2d2d2d')
        self._btn_mcpacker_remove.grid(row=0, column=1, padx=(6, 0), sticky="ew")

        # Configure resizing for files frame
        self._frame_mcpacker_files.grid_columnconfigure(0, weight=1)
        self._frame_mcpacker_files.grid_rowconfigure(0, weight=1)  # Listbox frame - expandable
        self._frame_mcpacker_files.grid_rowconfigure(1, weight=0)  # File count - fixed
        self._frame_mcpacker_files.grid_rowconfigure(2, weight=0)  # Buttons - fixed

        # LabelFrame for output directory selection - Modern styling
        self._frame_mcpacker_output = _tk.LabelFrame(self.mcpacker_frame, text="📂 " + _("app.select_output_dir"), bg='#1a1a1a', fg='#FFFFFF', font=("Segoe UI", 13, "bold"))
        self._frame_mcpacker_output.grid(row=1, column=0, padx=15, pady=(8, 8), sticky="nsew")

        self.output_dir_var = _tk.StringVar()

        # Output Directory Entry - Modern styling
        self._entry_mcpacker_output = _tk.Entry(self._frame_mcpacker_output, textvariable=self.output_dir_var, width=50, bg='#0A0A0A', fg='#FFFFFF', font=("Segoe UI", 11), insertbackground='#a855f7', relief='flat', highlightthickness=1, highlightbackground='#1a1a1a', highlightcolor='#9333ea')
        self._entry_mcpacker_output.grid(row=0, column=0, padx=12, pady=8, sticky="ew", ipady=6)
        # Browse Button for selecting output directory - Modern styling
        self._btn_mcpacker_browse_output = _tk.Button(self._frame_mcpacker_output, text=_("app.browse"), command=self.select_output_directory, bg='#9333ea', fg='#FFFFFF', font=("Segoe UI", 11, "bold"), relief='flat', cursor='hand2', activebackground='#a855f7')
        self._btn_mcpacker_browse_output.grid(row=0, column=1, padx=(0, 12), pady=8, sticky="ew")

        # Configure resizing for output frame
        self._frame_mcpacker_output.grid_columnconfigure(0, weight=1)

        # Progress Display Section - MCPACKER processing progress
        self._frame_mcpacker_progress = _tk.LabelFrame(self.mcpacker_frame, text="📊 " + _("app.processing_progress"), bg='#1a1a1a', fg='#FFFFFF', font=("Segoe UI", 13, "bold"))
        self._frame_mcpacker_progress.grid(row=2, column=0, padx=15, pady=(8, 8), sticky="nsew")
        self._frame_mcpacker_progress.columnconfigure(0, weight=1)
        self._frame_mcpacker_progress.grid_rowconfigure(0, weight=0)  # Progress container - fixed height
        
        progress_container = _tk.Frame(self._frame_mcpacker_progress, bg='#1a1a1a')
        progress_container.grid(row=0, column=0, padx=12, pady=(8, 8), sticky="nsew")
        progress_container.columnconfigure(0, weight=1)
        progress_container.rowconfigure(0, weight=0)  # Step label - fixed
        progress_container.rowconfigure(1, weight=0)  # Progress bar - fixed
        progress_container.rowconfigure(2, weight=0)  # Steps frame - fixed
        
        # Current step label
        self._mcpacker_progress_step_label = _tk.Label(progress_container, text=_("app.ready_to_process"), 
                                             bg='#1a1a1a', fg='#FFFFFF', 
                                             font=('Segoe UI', 11, 'bold'),
                                             anchor='center')
        self._mcpacker_progress_step_label.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        
        # Progress bar
        style = _ttk.Style()
        style.theme_use('clam')
        style.configure("MCPackerProgress.Horizontal.TProgressbar", background='#9333ea', troughcolor='#0A0A0A', borderwidth=0)
        self._mcpacker_progress = _ttk.Progressbar(progress_container, orient='horizontal', 
                                         length=400, mode='determinate', 
                                         style="MCPackerProgress.Horizontal.TProgressbar",
                                         maximum=100)
        self._mcpacker_progress.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        
        # Steps indicator (4 steps for MCPACKER)
        steps_frame = _tk.Frame(progress_container, bg='#1a1a1a')
        steps_frame.grid(row=2, column=0, sticky="ew", pady=(0, 0))
        steps_frame.grid_columnconfigure(0, weight=1)
        steps_frame.grid_columnconfigure(1, weight=1)
        steps_frame.grid_columnconfigure(2, weight=1)
        steps_frame.grid_columnconfigure(3, weight=1)
        
        self._mcpacker_step_labels = []
        # Step names will be updated based on mode (step 2 label switches to Extracting when in extract mode)
        step_names = [_("progress.reading_files"), _("progress.finding_packs"), _("progress.packaging_files"), _("progress.finalizing")]
        for i, step_name in enumerate(step_names):
            step_frame = _tk.Frame(steps_frame, bg='#1a1a1a')
            step_frame.grid(row=0, column=i, padx=3, sticky="")
            
            # Step number/status indicator
            step_status = _tk.Label(step_frame, text="○", bg='#1a1a1a', fg='#666666',
                                   font=('Segoe UI', 12), width=2, anchor='w')
            step_status.pack(side='left')
            self._mcpacker_step_labels.append({'status': step_status, 'name': step_name})
            
            # Step name
            step_label = _tk.Label(step_frame, text=step_name, bg='#1a1a1a', fg='#999999',
                                  font=('Segoe UI', 8))
            step_label.pack(side='left')
            self._mcpacker_step_labels[i]['label'] = step_label

        # Frame for the start button - Modern styling
        self._frame_mcpacker_controls = _tk.Frame(self.mcpacker_frame, bg='#000000')
        self._frame_mcpacker_controls.grid(row=3, column=0, padx=15, pady=(8, 8), sticky="ew")

        # Start Button for initiating the process - Modern styling
        self._btn_mcpacker_start = _tk.Button(self._frame_mcpacker_controls, text="🚀 " + _("mcpacker.start"), command=self.start_mcpacker, bg='#9333ea', fg='#FFFFFF', font=("Segoe UI", 12, "bold"), relief='flat', cursor='hand2', activebackground='#a855f7', padx=20, pady=10)
        self._btn_mcpacker_start.grid(row=0, column=0, padx=0, pady=0, sticky="ew")

        # Configure grid layout for controls
        self._frame_mcpacker_controls.grid_columnconfigure(0, weight=1)
        
        # Now configure mcpacker_frame for proper resizing after all widgets are created
        self.mcpacker_frame.grid_columnconfigure(0, weight=1)
        self.mcpacker_frame.grid_rowconfigure(0, weight=1, minsize=200)  # Files frame - expandable with minimum size
        self.mcpacker_frame.grid_rowconfigure(1, weight=0)  # Output frame - fixed
        self.mcpacker_frame.grid_rowconfigure(2, weight=0)  # Progress frame - fixed (don't shrink)
        self.mcpacker_frame.grid_rowconfigure(3, weight=0)  # Controls frame - fixed

    def init_list_maker_tab(self):
        # Frame for List Maker Tab - Modern styling
        self._frame_list_maker = _tk.LabelFrame(self.list_maker_frame, text="📋 " + _("list_maker.title"), bg='#1a1a1a', fg='#FFFFFF', font=("Segoe UI", 13, "bold"))
        self._frame_list_maker.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")

        # Mode Selection - Modern styling
        self.mode_var = _tk.StringVar(value="merged")
        self.mode_label = _tk.Label(self._frame_list_maker, text=_f("list_maker.mode", mode=_("list_maker.merged")), bg='#1a1a1a', fg='#FFFFFF', font=("Segoe UI", 12, "bold"))
        self.mode_label.grid(row=0, column=0, padx=12, pady=(12, 8), sticky="w")

        self._radio_merged = _tk.Radiobutton(self._frame_list_maker, text=_("list_maker.merged_list"), variable=self.mode_var, value="merged",
                        bg='#1a1a1a', fg='#FFFFFF', selectcolor='#9333ea', font=("Segoe UI", 11),
                        activebackground='#1a1a1a', activeforeground='#FFFFFF', command=self.update_mode_label)
        self._radio_merged.grid(row=1, column=0, padx=12, pady=5, sticky="w")
        
        self._radio_alone = _tk.Radiobutton(self._frame_list_maker, text=_("list_maker.alone_list"), variable=self.mode_var, value="alone",
                        bg='#1a1a1a', fg='#FFFFFF', selectcolor='#9333ea', font=("Segoe UI", 11),
                        activebackground='#1a1a1a', activeforeground='#FFFFFF', command=self.update_mode_label)
        self._radio_alone.grid(row=2, column=0, padx=12, pady=5, sticky="w")

        # Add Files Button - Modern styling
        self._btn_add_files = _tk.Button(self._frame_list_maker, text="➕ " + _("list_maker.add_files"), command=self.on_add_files,
                                         bg='#9333ea', fg='#FFFFFF', font=("Segoe UI", 11, "bold"), relief='flat', cursor='hand2', activebackground='#a855f7')
        self._btn_add_files.grid(row=3, column=0, padx=12, pady=12, sticky="ew")

        # File list with pack icon + name (scrollable)
        self._list_maker_photo_refs = []
        list_maker_list_frame = _tk.Frame(self._frame_list_maker, bg='#1a1a1a')
        list_maker_list_frame.grid(row=4, column=0, padx=12, pady=12, sticky="nsew")
        list_maker_list_frame.grid_columnconfigure(0, weight=1)
        list_maker_list_frame.grid_rowconfigure(0, weight=1)
        self._list_maker_canvas = _tk.Canvas(list_maker_list_frame, bg='#0A0A0A', highlightthickness=0)
        self._list_maker_canvas.grid(row=0, column=0, sticky="nsew")
        self._list_maker_inner = _tk.Frame(self._list_maker_canvas, bg='#0A0A0A')
        self._list_maker_canvas_window = self._list_maker_canvas.create_window(0, 0, window=self._list_maker_inner, anchor='nw')
        self._list_maker_inner.bind('<Configure>', lambda e: (self._list_maker_canvas.configure(scrollregion=self._list_maker_canvas.bbox('all')), self._list_maker_canvas.itemconfig(self._list_maker_canvas_window, width=e.width)))
        self._list_maker_canvas.bind('<Configure>', lambda e: self._list_maker_canvas.itemconfig(self._list_maker_canvas_window, width=e.width))
        def _list_maker_wheel(e):
            self._list_maker_canvas.yview_scroll(int(-1 * (e.delta / 120)), 'units')
        def _list_maker_scroll_enter(e):
            self._list_maker_canvas.bind_all('<MouseWheel>', _list_maker_wheel)
        def _list_maker_scroll_leave(e):
            try:
                self._list_maker_canvas.unbind_all('<MouseWheel>')
            except Exception:
                pass
        self._list_maker_canvas.bind('<Enter>', _list_maker_scroll_enter)
        self._list_maker_canvas.bind('<Leave>', _list_maker_scroll_leave)
        self._list_maker_inner.bind('<Enter>', _list_maker_scroll_enter)
        self._list_maker_inner.bind('<Leave>', _list_maker_scroll_leave)

        # Export List Button - Modern styling
        self._btn_export_list = _tk.Button(self._frame_list_maker, text="💾 " + _("list_maker.export_list"), command=self.export_list,
                                           bg='#9333ea', fg='#FFFFFF', font=("Segoe UI", 11, "bold"), relief='flat', cursor='hand2', activebackground='#a855f7')
        self._btn_export_list.grid(row=5, column=0, padx=12, pady=12, sticky="ew")

        # Configure resizing for List Maker frame
        self._frame_list_maker.grid_columnconfigure(0, weight=1)
        self._frame_list_maker.grid_rowconfigure(4, weight=1)

    def update_mode_label(self):
        mode_key = "list_maker.merged" if self.mode_var.get() == "merged" else "list_maker.alone"
        self.mode_label.config(text=_f("list_maker.mode", mode=_(mode_key)))

    def on_add_files(self):
        files = _filedialog.askopenfilenames(
            title=_("filedialog.select_mcpacks"),
            filetypes=[("MCPack Files", "*.mcpack")]
        )
        self.selected_files = list(files)
        self.update_file_list()

    def update_file_list(self):
        for w in self._list_maker_inner.winfo_children():
            w.destroy()
        self._list_maker_photo_refs.clear()
        for file_path in self.selected_files:
            display_name, photo, full_photo = self._get_pack_display_info(file_path)
            row = _tk.Frame(self._list_maker_inner, bg='#0A0A0A', height=52)
            row.pack(fill='x', padx=4, pady=2)
            row.pack_propagate(False)
            if photo:
                self._list_maker_photo_refs.append(photo)
                if full_photo:
                    self._list_maker_photo_refs.append(full_photo)
                icon_lbl = _tk.Label(row, image=photo, bg='#0A0A0A')
            else:
                icon_lbl = _tk.Label(row, text='\u26fa', font=('Segoe UI', 20), bg='#0A0A0A', fg='#666666')
            icon_lbl.pack(side=_tk.LEFT, padx=(8, 10), pady=6)
            name_lbl = _tk.Label(row, text=display_name, bg='#0A0A0A', fg='#FFFFFF', font=('Segoe UI', 10), anchor='w')
            name_lbl.pack(side=_tk.LEFT, fill='x', expand=True, pady=6)
        self._list_maker_canvas.configure(scrollregion=self._list_maker_canvas.bbox('all'))

    def clean_file_name(self, file_name):
        cleaned_name = _re.sub(r"_", " ", file_name)
        cleaned_name = _re.sub(r"\d+", "", cleaned_name)
        cleaned_name = _re.sub(r"\.mcpack", "", cleaned_name)
        return cleaned_name.strip()

    def export_list(self):
        if not self.selected_files:
            _messagebox.showwarning("No Files Selected", "Please select MCPack files to export.")
            return

        mode = self.mode_var.get()
        self.organize_and_export(self.selected_files, mode)

    def organize_and_export(self, selected_files, mode):
        output_lines = []
        total_size = 0

        if mode == "merged":
            output_lines.append("--- MERGE THESE ADDONS IF MERGE SELECTED ---\n\n")
        else:
            output_lines.append("--- ADD THESE ALONE ONLY ---\n\n")

        output_lines.append(f"{'ADDON NAME'.ljust(40)}| {'DATE ADDED'.ljust(15)}| TYPE   | SIZE\n")
        output_lines.append("-" * 80 + "\n")

        for file in selected_files:
            file_name = _os.path.basename(file)
            cleaned_name = self.clean_file_name(file_name)
            date_added = self.get_file_creation_date(file)
            pack_type, size = self.get_pack_type_and_size(file)

            total_size += float(size.split()[0])
            output_lines.append(f"{cleaned_name.ljust(40)}| {date_added.ljust(15)}| {pack_type.ljust(8)}| {size}\n")

        output_lines.append("-" * 80 + "\n")
        output_lines.append(f"FILE SIZE TOTAL: {total_size:.2f} MB\n")

        output_file = _filedialog.asksaveasfilename(
            title=_("filedialog.save_output"),
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt")]
        )

        if output_file:
            write_text_file_utf8(output_file, ''.join(output_lines))
            # Check for suspicious characters
            content = read_text_file_utf8_strip_bom(output_file)
            if '' in content or 'Â§' in content or 'Ã§' in content:
                with open(_LOG_PATH, "a", encoding="utf-8") as log_f:
                    log_f.write(f"Warning: Suspicious character found in {output_file}\n")
            _messagebox.showinfo(_("export.success_title"), _f("export.success_msg", path=output_file))
            self.reset_list_maker()

    def reset_list_maker(self):
        self.selected_files = []
        self.update_file_list()
        self.mode_var.set("merged")
        self.mode_label.config(text=_f("list_maker.mode", mode=_("list_maker.merged")))

    def get_file_creation_date(self, file_path):
        try:
            creation_time = _os.path.getctime(file_path)
            return _datetime.datetime.fromtimestamp(creation_time).strftime("%m/%d/%Y")
        except Exception:
            return "Unknown Date"

    def get_pack_type_and_size(self, file_path):
        try:
            manifest_data = self._get_manifest_data(file_path)
            if manifest_data and 'modules' in manifest_data and len(manifest_data['modules']) > 0:
                pack_type = "Resource" if manifest_data["modules"][0]["type"] == "resources" else "Behavior"
                file_size = _os.path.getsize(file_path) / (1024 * 1024)
                return pack_type, f"{file_size:.2f} MB"
            return "Unknown", "0.00 MB"
        except Exception:
            return "Unknown", "0.00 MB"
    
    def _detect_pack_type(self, file_path):
        """Detect if a .mcpack/.mcaddon file is a Behavior Pack (BP), Resource Pack (RP), or both.
        Returns: 'BP', 'RP', 'BP+RP', or 'Unknown'"""
        try:
            with _zipfile.ZipFile(file_path, 'r') as zip_file:
                # Find manifest.json in the zip
                manifest_path = None
                for filename in zip_file.namelist():
                    # Look for manifest.json at root level (not in subdirectories)
                    if filename.lower() == "manifest.json" or filename.lower().endswith("/manifest.json"):
                        # Prefer root level manifest
                        if filename.lower() == "manifest.json":
                            manifest_path = filename
                            break
                        elif manifest_path is None:
                            manifest_path = filename
                
                if manifest_path:
                    # Use the improved _get_manifest_data method which handles comments properly
                    manifest = self._get_manifest_data(file_path)
                    if manifest:
                        modules = manifest.get("modules", [])
                        
                        has_behavior = False
                        has_resource = False
                        
                        for module in modules:
                            module_type = module.get("type", "").lower()
                            if module_type in ("data", "script"):
                                has_behavior = True
                            elif module_type == "resources":
                                has_resource = True
                        
                        if has_behavior and has_resource:
                            return "BP+RP"
                        elif has_behavior:
                            return "BP"
                        elif has_resource:
                            return "RP"
                        else:
                            return "Unknown"
            return "Unknown"
        except Exception as e:
            return "Unknown"

    @staticmethod
    def _version_to_group_key(ver):
        """Convert an exact @minecraft/server version string to a broad grouping key.

        Groups by major version + stability so minor-version differences within the same
        major are merged together (they are backwards-compatible inside Bedrock):
            '1.5.0'      -> '1_x'
            '1.19.0'     -> '1_x'   (same group as 1.5.0)
            '2.0.0'      -> '2_x'
            '2.6.0'      -> '2_x'   (same group as 2.0.0)
            '2.5.0-beta' -> '2_x_beta'
            '2.7.0-beta' -> '2_x_beta'  (same group)
            '3.0.0-alpha'-> '3_x_alpha'
        """
        if not ver:
            return "none"
        v = str(ver).strip().lower()
        is_alpha   = 'alpha'   in v
        is_beta    = not is_alpha and any(s in v for s in ('beta', 'preview', 'rc'))
        m = _re.match(r'^(\d+)', v)
        if not m:
            return "none"
        major = m.group(1)
        if is_alpha:
            return f"{major}_x_alpha"
        elif is_beta:
            return f"{major}_x_beta"
        else:
            return f"{major}_x"

    def _group_files_by_script_api_version(self, file_list):
        """Group .mcpack/.mcaddon file paths by script API version bucket.
        Returns dict: folder_key (e.g. '1_x', '2_x', '2_x_beta', 'none') -> list of paths.

        Packs within the same major version are merged together — minor versions are
        backwards-compatible inside Bedrock (it promotes them automatically).

        Two-pass strategy so paired BP/RP halves always land in the same group:
          Pass 1 — assign every pack to its major-version bucket (BP packs get a real
                   version key; RP-only packs tentatively go to 'none').
          Pass 2 — for each RP pack in 'none', look for a BP pack with the same base name
                   in a versioned group; if found, move the RP into that same group so the
                   behavior and resource halves of the addon end up in one merged output.
        """
        # Pass 1: classify every file
        file_group = {}   # file_path -> folder_key
        rp_files = []     # RP-only packs (tentatively 'none')

        for file_path in file_list:
            folder_key = "none"
            try:
                manifest = self._get_manifest_data(file_path)
                if not manifest:
                    file_group[file_path] = folder_key
                    continue
                modules = manifest.get("modules") or []
                is_rp_only = (
                    isinstance(modules, list) and len(modules) > 0 and
                    isinstance(modules[0], dict) and
                    modules[0].get("type") == "resources"
                )
                if is_rp_only:
                    file_group[file_path] = "none"
                    rp_files.append(file_path)
                    continue
                ver = self._get_pack_script_api_version(manifest)
                if ver:
                    folder_key = self._version_to_group_key(ver)
                file_group[file_path] = folder_key
            except Exception:
                file_group[file_path] = folder_key

        # Pass 2: pair each RP file with its BP counterpart (if any)
        # Build a map: base_name -> version_key for all BP files in a versioned group
        bp_base_to_version = {}
        for fp, vk in file_group.items():
            if vk != "none" and fp not in rp_files:
                base = IdentifierManager._pack_base_name(fp)
                bp_base_to_version[base] = vk

        for rp_path in rp_files:
            base = IdentifierManager._pack_base_name(rp_path)
            matched_ver = bp_base_to_version.get(base)
            if matched_ver:
                file_group[rp_path] = matched_ver

        # Build final groups dict
        groups = defaultdict(list)
        for fp, vk in file_group.items():
            groups[vk].append(fp)
        return dict(groups)

    def _get_pack_display_info(self, file_path):
        """Get pack display name (from manifest header) and pack_icon as a Tk PhotoImage thumbnail.
        Returns (display_name, photo_image_or_None). Uses filename + pack type if manifest unavailable."""
        default_name = _os.path.basename(file_path)
        pack_type = self._detect_pack_type(file_path)
        if pack_type != "Unknown":
            default_display = f"{default_name} [{pack_type}]"
        else:
            default_display = default_name
        display_name = default_display
        photo = None
        full_photo = None
        pack_name = None
        try:
            manifest = self._get_manifest_data(file_path)
            if manifest:
                header = manifest.get("header") or {}
                name_val = header.get("name")
                if isinstance(name_val, str):
                    pack_name = name_val.strip() or default_name
                elif isinstance(name_val, dict):
                    pack_name = name_val.get("text") or name_val.get("translate") or default_name
                    if isinstance(pack_name, dict):
                        pack_name = (list(pack_name.values()) or [default_name])[0]
                    pack_name = str(pack_name).strip() if pack_name else default_name
                else:
                    pack_name = default_name
            else:
                pack_name = default_name

            # Resolve localization key names like "pack.name" from texts/en_US.(lang|json)
            resolved_name = None
            try:
                key = str(pack_name).strip() if pack_name else ''
                if key and key != default_name and (' ' not in key):
                    with _zipfile.ZipFile(file_path, 'r') as _zf:
                        candidates = [
                            'texts/en_US.lang',
                            'texts/en_US.json',
                            'R/texts/en_US.lang',
                            'R/texts/en_US.json',
                            'B/texts/en_US.lang',
                            'B/texts/en_US.json',
                        ]
                        for path in candidates:
                            try:
                                raw = _zf.read(path)
                            except KeyError:
                                continue
                            try:
                                text = raw.decode('utf-8')
                            except Exception:
                                text = raw.decode('latin-1', errors='ignore')
                            if path.endswith('.lang'):
                                m = _parse_lang_kv(text)
                                if key in m:
                                    resolved_name = m.get(key)
                                    break
                            else:
                                try:
                                    data = _json.loads(text)
                                except Exception:
                                    data = None
                                if isinstance(data, dict) and key in data:
                                    resolved_name = str(data.get(key))
                                    break
                if resolved_name:
                    pack_name = resolved_name.strip() or pack_name
            except Exception:
                pass

            display_name = f"{pack_name} [{pack_type}]" if pack_type != "Unknown" else pack_name
        except Exception:
            display_name = default_display
            pack_name = default_name
        try:
            with _zipfile.ZipFile(file_path, 'r') as zf:
                # Prefer icon from same directory as manifest (root, then behavior_pack, then first subdir)
                manifest_path = None
                root_m, bp_m, first_m = None, None, None
                for name in zf.namelist():
                    name_norm = name.replace('\\', '/')
                    name_lower = name_norm.lower()
                    if name_lower == 'manifest.json':
                        root_m = name_norm
                        break
                    if name_lower.endswith('/manifest.json'):
                        if first_m is None:
                            first_m = name_norm
                        if 'behavior_pack' in name_lower:
                            bp_m = name_norm
                if root_m:
                    manifest_path = root_m
                elif bp_m:
                    manifest_path = bp_m
                elif first_m:
                    manifest_path = first_m
                manifest_dir = (_os.path.dirname(manifest_path) + '/') if manifest_path else ''
                icon_name = None
                icon_in_manifest_dir = None
                manifest_dir_lower = manifest_dir.lower() if manifest_dir else ''
                for n in zf.namelist():
                    n_norm = n.replace('\\', '/')
                    n_lower = n_norm.lower()
                    if not (n_lower.endswith('pack_icon.png') or n_lower.endswith('pack_icon.jpg') or n_lower.endswith('pack_icon.jpeg')):
                        continue
                    if manifest_dir_lower and n_lower.startswith(manifest_dir_lower):
                        icon_in_manifest_dir = n_norm
                        break
                    if icon_name is None:
                        icon_name = n_norm
                if icon_in_manifest_dir:
                    icon_name = icon_in_manifest_dir
                if icon_name:
                    data = zf.read(icon_name)
                    # Prefer PIL/Pillow: Tk's PhotoImage often fails on some PNGs on Windows
                    if _PIL_AVAILABLE and data:
                        try:
                            img = _PIL_Image.open(io.BytesIO(data))
                            # Handle RGBA/P: composite onto white so transparency doesn't become black
                            if img.mode in ('RGBA', 'LA', 'P'):
                                if img.mode == 'P' and 'transparency' in img.info:
                                    img = img.convert('RGBA')
                                bg = _PIL_Image.new('RGB', img.size, (255, 255, 255))
                                if img.mode in ('RGBA', 'LA'):
                                    bg.paste(img, mask=img.split()[-1])
                                else:
                                    bg.paste(img)
                                img = bg
                            elif img.mode not in ('RGB', 'L'):
                                img = img.convert('RGB')
                            if img.mode == 'L':
                                img = img.convert('RGB')
                            thumb_resample = getattr(_PIL_Image.Resampling, 'LANCZOS', None) or getattr(_PIL_Image, 'LANCZOS', 1)
                            img.thumbnail((48, 48), thumb_resample)
                            photo = _PIL_ImageTk.PhotoImage(img)
                            return (display_name, photo, None)
                        except Exception:
                            # PIL decoded OK but PhotoImage failed; re-encode to simple PNG and try Tk from file
                            try:
                                img = _PIL_Image.open(io.BytesIO(data))
                                if img.mode in ('RGBA', 'LA', 'P'):
                                    if img.mode == 'P' and 'transparency' in img.info:
                                        img = img.convert('RGBA')
                                    bg = _PIL_Image.new('RGB', img.size, (255, 255, 255))
                                    if img.mode in ('RGBA', 'LA'):
                                        bg.paste(img, mask=img.split()[-1])
                                    else:
                                        bg.paste(img)
                                    img = bg
                                elif img.mode not in ('RGB', 'L'):
                                    img = img.convert('RGB')
                                if img.mode == 'L':
                                    img = img.convert('RGB')
                                img.thumbnail((48, 48), getattr(_PIL_Image.Resampling, 'LANCZOS', 1) or 1)
                                fd, tmp = _tempfile.mkstemp(suffix='.png')
                                _os.close(fd)
                                img.save(tmp, 'PNG')
                                full_photo = _tk.PhotoImage(file=tmp)
                                scale = max(1, min(full_photo.width(), full_photo.height()) // 48)
                                photo = full_photo.subsample(scale, scale)
                                try:
                                    _os.unlink(tmp)
                                except Exception:
                                    pass
                                return (display_name, photo, full_photo)
                            except Exception:
                                pass
                    # Fallback: Tk PhotoImage from temp file
                    ext = '.png' if icon_name.lower().endswith('.png') else '.jpg'
                    fd, tmp = _tempfile.mkstemp(suffix=ext)
                    try:
                        _os.write(fd, data)
                        _os.close(fd)
                        full_photo = _tk.PhotoImage(file=tmp)
                        w, h = full_photo.width(), full_photo.height()
                        scale = max(1, min(w, h) // 48)
                        photo = full_photo.subsample(scale, scale)
                        return (display_name, photo, full_photo)
                    except Exception:
                        pass
                    finally:
                        try:
                            _os.unlink(tmp)
                        except Exception:
                            pass
        except Exception:
            pass
        return (display_name, None, None)

    def init_help_tab(self):
        # Main container with split layout (navigation + content)
        main_container = _tk.Frame(self.help_frame, bg='#000000')
        main_container.pack(fill='both', expand=True, padx=15, pady=15)
        
        # Left navigation panel; width responds to window size so it fits on small screens
        nav_frame = _tk.Frame(main_container, bg='#1a1a1a', width=260)
        nav_frame.pack(side='left', fill='y', padx=(0, 15))
        nav_frame.pack_propagate(False)
        def _help_nav_resize(event):
            try:
                w = max(180, min(260, event.width // 3))
                if nav_frame.winfo_exists():
                    nav_frame.configure(width=w)
                    for child in nav_frame.winfo_children():
                        try:
                            if child.winfo_class() == 'Button':
                                child.configure(wraplength=max(120, w - 30))
                        except Exception:
                            pass
            except Exception:
                pass
        main_container.bind('<Configure>', _help_nav_resize)
        
        # Navigation title
        nav_title = _tk.Label(nav_frame, text="📚 " + _("help.nav_topics"), bg='#1a1a1a', fg='#FFFFFF', 
                             font=("Segoe UI", 13, "bold"))
        nav_title.pack(pady=(15, 20))
        
        # Navigation buttons
        self.help_sections = {}
        _help_nav_keys = {"Overview": "help.overview", "Getting Started": "help.getting_started", "What Happens During Merging": "help.merging", "Common Errors": "help.common_errors", "Best Practices": "help.best_practices", "Processing Overview": "help.processing_overview", "Important Notes": "help.important_notes"}
        nav_buttons = [
            ("Overview", "📌"),
            ("Getting Started", "🚀"),
            ("What Happens During Merging", "📦"),
            ("Common Errors", "⚠️"),
            ("Best Practices", "💡"),
            ("Processing Overview", "⚙️"),
            ("Important Notes", "📋"),
            ("Modpack Organization", "📊")
        ]
        
        self.current_help_section = _tk.StringVar(value="Overview")
        
        for section_name, icon in nav_buttons:
            btn = _tk.Button(nav_frame, 
                           text=f"{icon} {_(_help_nav_keys.get(section_name, section_name))}",
                           command=lambda s=section_name: self._show_help_section(s),
                           bg='#0A0A0A', fg='#FFFFFF', font=("Segoe UI", 10),
                           relief='flat', anchor='w', padx=15, pady=12,
                           cursor='hand2', activebackground='#9333ea', activeforeground='#FFFFFF',
                           wraplength=230, justify='left')
            btn.pack(fill='x', padx=10, pady=5)
            self.help_sections[section_name] = btn
        
        # Right content area with scrollable canvas
        content_container = _tk.Frame(main_container, bg='#000000')
        content_container.pack(side='right', fill='both', expand=True)
        
        # Create canvas with hover-scroll only (no visible scrollbar)
        canvas = _tk.Canvas(content_container, bg='#000000', highlightthickness=0)
        self.help_content_frame = _tk.Frame(canvas, bg='#000000')
        
        def update_scroll_region(event=None):
            canvas.update_idletasks()
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        self.help_content_frame.bind("<Configure>", update_scroll_region)
        
        canvas.create_window((0, 0), window=self.help_content_frame, anchor="nw")
        
        # Update canvas width and help text wraplength when resized so content fits the window
        def set_wraplength_recursive(widget, wraplen):
            try:
                if widget.winfo_class() == 'Label':
                    widget.configure(wraplength=max(200, wraplen))
                for child in widget.winfo_children():
                    set_wraplength_recursive(child, wraplen)
            except Exception:
                pass
        def configure_canvas_width(event):
            canvas_width = event.width
            if canvas.find_all():
                canvas.itemconfig(canvas.find_all()[0], width=canvas_width)
            set_wraplength_recursive(self.help_content_frame, canvas_width - 40)
        canvas.bind('<Configure>', configure_canvas_width)
        
        # Pack canvas (no scrollbar shown)
        canvas.pack(side="left", fill="both", expand=True)

        # Hover-based mouse wheel scrolling (active only while cursor is over Help content)
        def _on_mousewheel(event):
            try:
                if canvas.winfo_exists():
                    canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            except Exception:
                pass
        def _help_scroll_bind_enter(event):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
        def _help_scroll_bind_leave(event):
            try:
                canvas.unbind_all("<MouseWheel>")
            except Exception:
                pass
        canvas.bind("<Enter>", _help_scroll_bind_enter)
        canvas.bind("<Leave>", _help_scroll_bind_leave)
        self.help_content_frame.bind("<Enter>", _help_scroll_bind_enter)
        self.help_content_frame.bind("<Leave>", _help_scroll_bind_leave)
        
        # Store canvas reference for scrolling
        self.help_canvas = canvas
        
        # Create all help sections (initially hidden)
        self._create_help_sections()
        
        # Show default section (Overview so users see what the app is and how it works first)
        self._show_help_section("Overview")
    
    def _open_discord_invite(self):
        """Open Discord invite link in default browser."""
        try:
            webbrowser.open("https://discord.gg/M8jDRZW8j4")
        except Exception as e:
            log_error(f"Failed to open Discord invite: {e}")
            _messagebox.showerror(_("msg.error"), _("error.discord_failed"))
    
    def _create_help_sections(self):
        """Create all help section content frames."""
        # Store all section frames
        self.help_section_frames = {}
        
        # Overview Section (what AutoBE is, the three tabs, activation)
        self.help_section_frames["Overview"] = self._create_overview_section()
        
        # Getting Started Section
        self.help_section_frames["Getting Started"] = self._create_getting_started_section()
        
        # What Happens During Merging Section
        self.help_section_frames["What Happens During Merging"] = self._create_merging_section()
        
        # Common Errors Section
        self.help_section_frames["Common Errors"] = self._create_errors_section()
        
        # Best Practices Section
        self.help_section_frames["Best Practices"] = self._create_best_practices_section()
        
        # Processing Overview Section
        self.help_section_frames["Processing Overview"] = self._create_processing_section()
        
        # Important Notes Section
        self.help_section_frames["Important Notes"] = self._create_disclaimer_section()
        
        # Modpack Organization Section
        self.help_section_frames["Modpack Organization"] = self._create_modpack_organization_section()
    
    def _show_help_section(self, section_name):
        """Show the selected help section and hide others."""
        # Hide all sections
        for frame in self.help_section_frames.values():
            frame.pack_forget()
        
        # Show selected section
        if section_name in self.help_section_frames:
            self.help_section_frames[section_name].pack(fill='both', expand=True, padx=0, pady=0)
            self.current_help_section.set(section_name)
            
            # Update button styles
            for name, btn in self.help_sections.items():
                if name == section_name:
                    btn.config(bg='#9333ea', fg='#FFFFFF')
                else:
                    btn.config(bg='#0A0A0A', fg='#FFFFFF')
            
            # Scroll to top and update scroll region
            self.help_canvas.yview_moveto(0)
            self.help_canvas.update_idletasks()
            # Force update of scroll region after showing section
            self._root.after(100, lambda: self.help_canvas.configure(scrollregion=self.help_canvas.bbox("all")))
            # Force update of scroll region after showing section
            self._root.after(100, lambda: self.help_canvas.configure(scrollregion=self.help_canvas.bbox("all")))
    
    def _create_overview_section(self):
        """Create the Overview help section: what AutoBE is, the three tabs, activation."""
        section_frame = _tk.Frame(self.help_content_frame, bg='#000000')
        
        overview_card = _tk.LabelFrame(section_frame, text="📌 " + _("help.overview"), 
                                       bg='#1a1a1a', fg='#FFFFFF', font=("Segoe UI", 14, "bold"),
                                       relief='flat', bd=0)
        overview_card.pack(fill='x', padx=0, pady=(0, 15))
        overview_inner = _tk.Frame(overview_card, bg='#1a1a1a')
        overview_inner.pack(fill='both', expand=True, padx=20, pady=15)
        
        _tk.Label(overview_inner, text=_("help.overview_what_is"), bg='#1a1a1a', fg='#FFFFFF',
                  font=("Segoe UI", 11), justify='left', anchor='w', wraplength=680).pack(fill='x', pady=(0, 15))
        
        _tk.Label(overview_inner, text=_("help.overview_tabs_intro"), bg='#1a1a1a', fg='#9333ea',
                  font=("Segoe UI", 11, "bold"), anchor='w').pack(fill='x', pady=(0, 8))
        _tk.Label(overview_inner, text=_("help.overview_tabs_autobe"), bg='#1a1a1a', fg='#CCCCCC',
                  font=("Segoe UI", 10), justify='left', anchor='w', wraplength=680).pack(fill='x', pady=(0, 6))
        _tk.Label(overview_inner, text=_("help.overview_tabs_mcpacker"), bg='#1a1a1a', fg='#CCCCCC',
                  font=("Segoe UI", 10), justify='left', anchor='w', wraplength=680).pack(fill='x', pady=(0, 6))
        _tk.Label(overview_inner, text=_("help.overview_tabs_list_maker"), bg='#1a1a1a', fg='#CCCCCC',
                  font=("Segoe UI", 10), justify='left', anchor='w', wraplength=680).pack(fill='x', pady=(0, 15))
        
        _tk.Label(overview_inner, text=_("help.overview_activation_intro"), bg='#1a1a1a', fg='#9333ea',
                  font=("Segoe UI", 11, "bold"), anchor='w').pack(fill='x', pady=(0, 8))
        _tk.Label(overview_inner, text=_("help.overview_activation"), bg='#1a1a1a', fg='#CCCCCC',
                  font=("Segoe UI", 10), justify='left', anchor='w', wraplength=680).pack(fill='x', pady=(0, 5))
        
        return section_frame
    
    def _create_getting_started_section(self):
        """Create the Getting Started help section."""
        section_frame = _tk.Frame(self.help_content_frame, bg='#000000')
        
        # Welcome Section
        welcome_card = _tk.LabelFrame(section_frame, text="📖 " + _("help.welcome"), 
                                     bg='#1a1a1a', fg='#FFFFFF', font=("Segoe UI", 14, "bold"),
                                     relief='flat', bd=0)
        welcome_card.pack(fill='x', padx=0, pady=(0, 15))
        
        welcome_inner = _tk.Frame(welcome_card, bg='#1a1a1a')
        welcome_inner.pack(fill='both', expand=True, padx=20, pady=15)
        
        welcome_text = _tk.Label(welcome_inner, 
                                 text=_("help.welcome_text"),
                                 bg='#1a1a1a', fg='#FFFFFF', font=("Segoe UI", 11),
                                 justify='left', anchor='w')
        welcome_text.pack(fill='x', pady=(0, 5))
        
        # Discord invite section
        discord_frame = _tk.Frame(welcome_inner, bg='#1a1a1a')
        discord_frame.pack(fill='x', pady=(10, 0))
        
        discord_label = _tk.Label(discord_frame,
                                 text=_("help.need_help_discord"),
                                 bg='#1a1a1a', fg='#FFFFFF', font=("Segoe UI", 10),
                                 justify='left', anchor='w')
        discord_label.pack(side='left', padx=(0, 10))
        
        discord_btn = _tk.Button(discord_frame,
                               text="💬 " + _("help.join_discord"),
                               command=lambda: self._open_discord_invite(),
                               bg='#5865F2', fg='#FFFFFF', font=("Segoe UI", 10, "bold"),
                               relief='flat', padx=15, pady=8,
                               cursor='hand2', activebackground='#4752C4', activeforeground='#FFFFFF')
        discord_btn.pack(side='left')
        
        # Complete Usage Guide Section
        usage_card = _tk.LabelFrame(section_frame, text="📚 " + _("help.usage_guide"), 
                                    bg='#1a1a1a', fg='#FFFFFF', font=("Segoe UI", 14, "bold"),
                                    relief='flat', bd=0)
        usage_card.pack(fill='both', expand=True, padx=0, pady=(0, 15))
        
        usage_inner = _tk.Frame(usage_card, bg='#1a1a1a')
        usage_inner.pack(fill='both', expand=True, padx=20, pady=15)
        
        usage_steps = [
            (_("help.usage1_title"), _("help.usage1_desc")),
            (_("help.usage2_title"), _("help.usage2_desc")),
            (_("help.usage3_title"), _("help.usage3_desc")),
            (_("help.usage4_title"), _("help.usage4_desc")),
            (_("help.usage5_title"), _("help.usage5_desc")),
        ]
        
        for i, (title, description) in enumerate(usage_steps, 1):
            step_frame = _tk.Frame(usage_inner, bg='#0A0A0A', relief='flat')
            step_frame.pack(fill='x', pady=(0, 10), padx=5)
            
            step_title = _tk.Label(step_frame, text=f"{i}. {title}", bg='#0A0A0A', fg='#9333ea',
                                   font=("Segoe UI", 11, "bold"), anchor='w')
            step_title.pack(fill='x', padx=12, pady=(10, 5))
            
            step_desc = _tk.Label(step_frame, text=description, bg='#0A0A0A', fg='#CCCCCC',
                                 font=("Segoe UI", 10), anchor='w', justify='left', wraplength=680)
            step_desc.pack(fill='x', padx=12, pady=(0, 10))

        # Music setup guide (background music + playlists + controls)
        music_card = _tk.LabelFrame(section_frame, text="🎵 Music Setup", 
                                    bg='#1a1a1a', fg='#FFFFFF', font=("Segoe UI", 14, "bold"),
                                    relief='flat', bd=0)
        music_card.pack(fill='x', padx=0, pady=(0, 15))
        music_inner = _tk.Frame(music_card, bg='#1a1a1a')
        music_inner.pack(fill='both', expand=True, padx=20, pady=15)

        _tk.Label(
            music_inner,
            text="How to set up music and playlists:",
            bg='#1a1a1a',
            fg='#9333ea',
            font=("Segoe UI", 11, "bold"),
            anchor='w'
        ).pack(fill='x', pady=(0, 8))

        music_steps = [
            "1) Put audio files in the app's music folder (supported: .mp3, .ogg, .wav).",
            "2) Optional playlists: create folders inside music (for example: music\\lofi, music\\hype).",
            "3) Open Settings -> Background music and enable 'Play background music'.",
            "4) Choose a Playlist (All music or a folder name), then set volume/shuffle.",
            "5) Use ⏮ and ⏭ in Settings to go previous/next instantly.",
            "6) The 'Now Playing' popup appears on each new track; long names scroll automatically.",
        ]
        for line in music_steps:
            _tk.Label(
                music_inner,
                text=line,
                bg='#1a1a1a',
                fg='#CCCCCC',
                font=("Segoe UI", 10),
                anchor='w',
                justify='left',
                wraplength=680
            ).pack(fill='x', pady=(0, 4))

        _tk.Label(
            music_inner,
            text="Tip: Name your default main track background.mp3 (or background.ogg/.wav) to make it the preferred first song.",
            bg='#1a1a1a',
            fg='#9ca3af',
            font=("Segoe UI", 9),
            anchor='w',
            justify='left',
            wraplength=680
        ).pack(fill='x', pady=(8, 0))
        
        return section_frame
    
    def _create_merging_section(self):
        """Create the Merging Process section."""
        section_frame = _tk.Frame(self.help_content_frame, bg='#000000')
        
        merging_card = _tk.LabelFrame(section_frame, text="📦 " + _("help.merging"), 
                                     bg='#1a1a1a', fg='#FFFFFF', font=("Segoe UI", 14, "bold"),
                                     relief='flat', bd=0)
        merging_card.pack(fill='both', expand=True, padx=0, pady=(0, 15))
        
        merging_inner = _tk.Frame(merging_card, bg='#1a1a1a')
        merging_inner.pack(fill='both', expand=True, padx=20, pady=15)
        
        merging_info = [
            (_("help.merge1_title"), _("help.merge1_desc")),
            (_("help.merge2_title"), _("help.merge2_desc")),
            (_("help.merge3_title"), _("help.merge3_desc")),
        ]
        
        for title, description in merging_info:
            info_frame = _tk.Frame(merging_inner, bg='#0A0A0A', relief='flat')
            info_frame.pack(fill='x', pady=(0, 12), padx=5)
            
            info_title = _tk.Label(info_frame, text=f"• {title}", bg='#0A0A0A', fg='#9333ea',
                                  font=("Segoe UI", 11, "bold"), anchor='w', wraplength=650)
            info_title.pack(fill='x', padx=12, pady=(12, 6))
            
            info_desc = _tk.Label(info_frame, text=description, bg='#0A0A0A', fg='#CCCCCC',
                                 font=("Segoe UI", 10), anchor='w', justify='left', wraplength=650)
            info_desc.pack(fill='x', padx=12, pady=(0, 12))

        # Practical merge workflow users can follow step-by-step
        workflow_card = _tk.Frame(merging_inner, bg='#0A0A0A', relief='flat')
        workflow_card.pack(fill='x', pady=(0, 12), padx=5)
        _tk.Label(workflow_card, text="• Complete merge workflow (recommended order)", bg='#0A0A0A', fg='#9333ea',
                  font=("Segoe UI", 11, "bold"), anchor='w', wraplength=650).pack(fill='x', padx=12, pady=(12, 6))
        workflow_steps = [
            "1) Add only valid .mcpack files in the AutoBE tab (remove duplicates before running).",
            "2) Set output folder to a clean location (empty/new folder is best).",
            "3) Choose whether to merge by script version in Settings if your packs mix API versions.",
            "4) Start process and wait for all 4 progress steps to complete.",
            "5) Optional after merge: use linked packs list, remove one addon, and re-merge automatically.",
            "6) Optional after merge: customize pack name/description/icon/author for final release.",
        ]
        for line in workflow_steps:
            _tk.Label(workflow_card, text=line, bg='#0A0A0A', fg='#CCCCCC', font=("Segoe UI", 10),
                      anchor='w', justify='left', wraplength=650).pack(fill='x', padx=12, pady=(0, 4))
        _tk.Label(workflow_card, text="Tip: keep original source packs unchanged; treat merged output as a build artifact.",
                  bg='#0A0A0A', fg='#9ca3af', font=("Segoe UI", 9), anchor='w', justify='left', wraplength=650).pack(fill='x', padx=12, pady=(8, 12))

        # Linked packs/remove flow documentation
        linked_card = _tk.Frame(merging_inner, bg='#0A0A0A', relief='flat')
        linked_card.pack(fill='x', pady=(0, 12), padx=5)
        _tk.Label(linked_card, text="• Linked packs: remove one addon from a merge", bg='#0A0A0A', fg='#9333ea',
                  font=("Segoe UI", 11, "bold"), anchor='w', wraplength=650).pack(fill='x', padx=12, pady=(12, 6))
        linked_steps = [
            "1) Run a merge at least once so _autobe_merge_manifest.json is created in output.",
            "2) Open linked packs (auto popup if enabled in Settings, or from linked packs flow).",
            "3) Click Remove on the addon you want to exclude.",
            "4) AutoBE re-runs the merge using remaining source packs and overwrites output.",
            "5) If source files moved/deleted, re-add valid packs and merge again.",
        ]
        for line in linked_steps:
            _tk.Label(linked_card, text=line, bg='#0A0A0A', fg='#CCCCCC', font=("Segoe UI", 10),
                      anchor='w', justify='left', wraplength=650).pack(fill='x', padx=12, pady=(0, 4))
        _tk.Label(linked_card, text="Important: at least one pack must remain; removing the last pack is blocked.",
                  bg='#0A0A0A', fg='#fca5a5', font=("Segoe UI", 9), anchor='w', justify='left', wraplength=650).pack(fill='x', padx=12, pady=(8, 12))

        # Script / API version behavior explanation
        script_card = _tk.Frame(merging_inner, bg='#0A0A0A', relief='flat')
        script_card.pack(fill='x', pady=(0, 4), padx=5)
        _tk.Label(script_card, text="• Script/API version handling", bg='#0A0A0A', fg='#9333ea',
                  font=("Segoe UI", 11, "bold"), anchor='w', wraplength=650).pack(fill='x', padx=12, pady=(12, 6))
        _tk.Label(script_card,
                  text="When packs use different @minecraft/server API versions, enable 'merge by script version' in Settings. AutoBE creates separate subfolders per version, reducing script conflicts and runtime breakage.",
                  bg='#0A0A0A', fg='#CCCCCC', font=("Segoe UI", 10), anchor='w', justify='left', wraplength=650).pack(fill='x', padx=12, pady=(0, 12))
        
        return section_frame
    
    def _create_errors_section(self):
        """Create the Common Errors section."""
        section_frame = _tk.Frame(self.help_content_frame, bg='#000000')
        
        errors_card = _tk.LabelFrame(section_frame, text="⚠️ " + _("help.common_errors_full"), 
                                    bg='#1a1a1a', fg='#FFFFFF', font=("Segoe UI", 14, "bold"),
                                    relief='flat', bd=0)
        errors_card.pack(fill='both', expand=True, padx=0, pady=(0, 15))
        
        errors_inner = _tk.Frame(errors_card, bg='#1a1a1a')
        errors_inner.pack(fill='both', expand=True, padx=20, pady=15)
        
        error_solutions = [
            (_("help.error1_title"), _("help.error1_desc")),
            (_("help.error2_title"), _("help.error2_desc")),
            (_("help.error3_title"), _("help.error3_desc")),
            (_("help.error4_title"), _("help.error4_desc")),
            (_("help.error5_title"), _("help.error5_desc")),
        ]
        
        for title, description in error_solutions:
            error_frame = _tk.Frame(errors_inner, bg='#0A0A0A', relief='flat')
            error_frame.pack(fill='x', pady=(0, 12), padx=5)
            
            error_title = _tk.Label(error_frame, text=title, bg='#0A0A0A', fg='#FF6B6B',
                                   font=("Segoe UI", 11, "bold"), anchor='w', wraplength=650)
            error_title.pack(fill='x', padx=12, pady=(12, 6))
            
            error_desc = _tk.Label(error_frame, text=description, bg='#0A0A0A', fg='#CCCCCC',
                                  font=("Segoe UI", 10), anchor='w', justify='left', wraplength=650)
            error_desc.pack(fill='x', padx=12, pady=(0, 12))

        # Troubleshooting matrix for real modpack merge failures
        quickfix_card = _tk.Frame(errors_inner, bg='#0A0A0A', relief='flat')
        quickfix_card.pack(fill='x', pady=(0, 12), padx=5)
        _tk.Label(quickfix_card, text="Quick fixes by symptom", bg='#0A0A0A', fg='#FF6B6B',
                  font=("Segoe UI", 11, "bold"), anchor='w', wraplength=650).pack(fill='x', padx=12, pady=(12, 8))
        quick_fixes = [
            "• 'No manifest.json' -> verify pack is a valid .mcpack/.mcaddon and not a random zip export.",
            "• Merge finishes but game crashes -> enable merge-by-script-version and test each output folder separately.",
            "• Textures/models missing -> check pack order and duplicate file collisions; retry with fewer packs to isolate.",
            "• Linked packs remove fails -> ensure source files still exist at original paths from merge manifest.",
            "• Update errors on Windows -> run app as admin and ensure antivirus did not quarantine the new exe.",
            "• Music not playing -> check Settings toggle, playlist selection, and supported audio file extensions.",
        ]
        for line in quick_fixes:
            _tk.Label(quickfix_card, text=line, bg='#0A0A0A', fg='#CCCCCC', font=("Segoe UI", 10),
                      anchor='w', justify='left', wraplength=650).pack(fill='x', padx=12, pady=(0, 4))
        _tk.Label(quickfix_card, text="Debug workflow: remove half the packs, re-merge, then binary-search the failing addon.",
                  bg='#0A0A0A', fg='#9ca3af', font=("Segoe UI", 9), anchor='w', justify='left', wraplength=650).pack(fill='x', padx=12, pady=(8, 12))
        
        return section_frame
    
    def _create_best_practices_section(self):
        """Create the Best Practices section."""
        section_frame = _tk.Frame(self.help_content_frame, bg='#000000')
        
        best_practices_card = _tk.LabelFrame(section_frame, text="💡 " + _("help.best_practices"), 
                                            bg='#1a1a1a', fg='#FFFFFF', font=("Segoe UI", 14, "bold"),
                                            relief='flat', bd=0)
        best_practices_card.pack(fill='both', expand=True, padx=0, pady=(0, 15))
        
        best_practices_inner = _tk.Frame(best_practices_card, bg='#1a1a1a')
        best_practices_inner.pack(fill='both', expand=True, padx=20, pady=15)
        
        practices = [
            _("help.practice1"), _("help.practice2"), _("help.practice3"), _("help.practice4"),
            _("help.practice5"), _("help.practice6"),
        ]
        
        for practice in practices:
            practice_label = _tk.Label(best_practices_inner, text=f"✓ {practice}", bg='#1a1a1a', fg='#CCCCCC',
                                      font=("Segoe UI", 10), anchor='w', justify='left', wraplength=650)
            practice_label.pack(fill='x', pady=(0, 8))
        
        return section_frame
    
    def _create_processing_section(self):
        """Create the Processing Overview section."""
        section_frame = _tk.Frame(self.help_content_frame, bg='#000000')
        
        processing_card = _tk.LabelFrame(section_frame, text="⚙️ " + _("help.processing_overview"), 
                                       bg='#1a1a1a', fg='#FFFFFF', font=("Segoe UI", 14, "bold"),
                                       relief='flat', bd=0)
        processing_card.pack(fill='both', expand=True, padx=0, pady=(0, 15))
        
        processing_inner = _tk.Frame(processing_card, bg='#1a1a1a')
        processing_inner.pack(fill='both', expand=True, padx=20, pady=15)
        
        processing_steps = [
            (_("help.proc1_title"), _("help.proc1_desc")),
            (_("help.proc2_title"), _("help.proc2_desc")),
            (_("help.proc3_title"), _("help.proc3_desc")),
            (_("help.proc4_title"), _("help.proc4_desc")),
        ]
        
        for title, description in processing_steps:
            step_frame = _tk.Frame(processing_inner, bg='#0A0A0A', relief='flat')
            step_frame.pack(fill='x', pady=(0, 10), padx=5)
            
            step_title = _tk.Label(step_frame, text=f"• {title}", bg='#0A0A0A', fg='#9333ea',
                                  font=("Segoe UI", 11, "bold"), anchor='w')
            step_title.pack(fill='x', padx=12, pady=(10, 5))
            
            step_desc = _tk.Label(step_frame, text=description, bg='#0A0A0A', fg='#CCCCCC',
                                 font=("Segoe UI", 10), anchor='w', justify='left', wraplength=680)
            step_desc.pack(fill='x', padx=12, pady=(0, 10))

        internals_card = _tk.Frame(processing_inner, bg='#0A0A0A', relief='flat')
        internals_card.pack(fill='x', pady=(0, 4), padx=5)
        _tk.Label(internals_card, text="How AutoBE processes your packs internally", bg='#0A0A0A', fg='#9333ea',
                  font=("Segoe UI", 11, "bold"), anchor='w').pack(fill='x', padx=12, pady=(12, 6))
        internals = [
            "• Reads pack manifests and detects subpacks/scripts/dependencies.",
            "• Optionally prompts for subpack choice and repacks selected variant.",
            "• Merges pack content and normalizes output structure.",
            "• Writes merge manifest used by linked-pack remove/re-merge flow.",
            "• Builds final behavior_pack.mcpack and resource_pack.mcpack artifacts.",
        ]
        for line in internals:
            _tk.Label(internals_card, text=line, bg='#0A0A0A', fg='#CCCCCC', font=("Segoe UI", 10),
                      anchor='w', justify='left', wraplength=680).pack(fill='x', padx=12, pady=(0, 4))
        _tk.Label(internals_card, text="Note: if any step fails, read the error, fix inputs, and run merge again from clean output.",
                  bg='#0A0A0A', fg='#9ca3af', font=("Segoe UI", 9), anchor='w', justify='left', wraplength=680).pack(fill='x', padx=12, pady=(8, 12))
        
        return section_frame
    
    def _create_disclaimer_section(self):
        """Create the Important Notes section."""
        section_frame = _tk.Frame(self.help_content_frame, bg='#000000')
        
        disclaimer_card = _tk.LabelFrame(section_frame, text="📋 " + _("help.important_notes_full"), 
                                         bg='#1a1a1a', fg='#FFFFFF', font=("Segoe UI", 14, "bold"),
                                         relief='flat', bd=0)
        disclaimer_card.pack(fill='both', expand=True, padx=0, pady=(0, 15))
        
        disclaimer_inner = _tk.Frame(disclaimer_card, bg='#1a1a1a')
        disclaimer_inner.pack(fill='both', expand=True, padx=20, pady=15)
        
        disclaimer_items = [
            (_("help.disc1_title"), _("help.disc1_desc")),
            (_("help.disc2_title"), _("help.disc2_desc")),
            (_("help.disc3_title"), _("help.disc3_desc")),
            (_("help.disc4_title"), _("help.disc4_desc")),
        ]
        
        for title, description in disclaimer_items:
            item_frame = _tk.Frame(disclaimer_inner, bg='#0A0A0A', relief='flat')
            item_frame.pack(fill='x', pady=(0, 12), padx=5)
            
            item_title = _tk.Label(item_frame, text=f"• {title}", bg='#0A0A0A', fg='#9333ea',
                                  font=("Segoe UI", 11, "bold"), anchor='w', wraplength=600)
            item_title.pack(fill='x', padx=12, pady=(12, 6))
            
            item_desc = _tk.Label(item_frame, text=description, bg='#0A0A0A', fg='#CCCCCC',
                                 font=("Segoe UI", 10), anchor='w', justify='left', wraplength=600)
            item_desc.pack(fill='x', padx=12, pady=(0, 12))
        
        # Footer
        footer_label = _tk.Label(section_frame, text=_("app.codenex"), 
                                 bg='#000000', fg='#666666', font=("Segoe UI", 9))
        footer_label.pack(fill='x', pady=(10, 20))
        
        return section_frame
    
    def _create_modpack_organization_section(self):
        """Create the Modpack Organization section."""
        section_frame = _tk.Frame(self.help_content_frame, bg='#000000')
        
        org_card = _tk.LabelFrame(section_frame, text="📊 Modpack Organization", 
                                 bg='#1a1a1a', fg='#FFFFFF', font=("Segoe UI", 14, "bold"),
                                 relief='flat', bd=0)
        org_card.pack(fill='both', expand=True, padx=0, pady=(0, 15))
        
        org_inner = _tk.Frame(org_card, bg='#1a1a1a')
        org_inner.pack(fill='both', expand=True, padx=20, pady=15)
        
        # What is it
        what_card = _tk.Frame(org_inner, bg='#0A0A0A', relief='flat')
        what_card.pack(fill='x', pady=(0, 12), padx=5)
        _tk.Label(what_card, text="What is Modpack Organization?", bg='#0A0A0A', fg='#9333ea',
                  font=("Segoe UI", 11, "bold"), anchor='w').pack(fill='x', padx=12, pady=(12, 6))
        _tk.Label(what_card, 
                  text="Modpack Organization helps you track and manage the addons in your merged modpacks using Excel or CSV files. After merging, you can create a configuration file that lists all addons, their versions, and metadata.",
                  bg='#0A0A0A', fg='#CCCCCC', font=("Segoe UI", 10), anchor='w', justify='left', wraplength=650).pack(fill='x', padx=12, pady=(0, 12))
        
        # How to enable
        enable_card = _tk.Frame(org_inner, bg='#0A0A0A', relief='flat')
        enable_card.pack(fill='x', pady=(0, 12), padx=5)
        _tk.Label(enable_card, text="How to Enable", bg='#0A0A0A', fg='#9333ea',
                  font=("Segoe UI", 11, "bold"), anchor='w').pack(fill='x', padx=12, pady=(12, 6))
        enable_steps = [
            "• Go to the Settings tab",
            "• Find the 'Modpack Organization' section",
            "• Check 'Enable Excel/CSV organization'",
            "• Click 'Save Settings'",
        ]
        for step in enable_steps:
            _tk.Label(enable_card, text=step, bg='#0A0A0A', fg='#CCCCCC', font=("Segoe UI", 10),
                      anchor='w', justify='left', wraplength=650).pack(fill='x', padx=12, pady=(0, 4))
        _tk.Label(enable_card, text="Once enabled, the organization prompt will appear automatically after each merge.",
                  bg='#0A0A0A', fg='#9ca3af', font=("Segoe UI", 9), anchor='w', justify='left', wraplength=650).pack(fill='x', padx=12, pady=(8, 12))
        
        # Workflow
        workflow_card = _tk.Frame(org_inner, bg='#0A0A0A', relief='flat')
        workflow_card.pack(fill='x', pady=(0, 12), padx=5)
        _tk.Label(workflow_card, text="Complete Workflow", bg='#0A0A0A', fg='#9333ea',
                  font=("Segoe UI", 11, "bold"), anchor='w').pack(fill='x', padx=12, pady=(12, 6))
        workflow_steps = [
            "1. Select your .mcpack files in the main UI",
            "2. Click '🚀 Start Process' to merge",
            "3. After merge completes, a dialog appears asking for modpack name",
            "4. Enter modpack name, min/max versions, and click 'Create Excel/CSV'",
            "5. The system creates a configuration file in your output directory",
            "6. Open the file in Excel or any spreadsheet application to view/edit",
        ]
        for step in workflow_steps:
            _tk.Label(workflow_card, text=step, bg='#0A0A0A', fg='#CCCCCC', font=("Segoe UI", 10),
                      anchor='w', justify='left', wraplength=650).pack(fill='x', padx=12, pady=(0, 4))
        
        # Manual management
        manual_card = _tk.Frame(org_inner, bg='#0A0A0A', relief='flat')
        manual_card.pack(fill='x', pady=(0, 12), padx=5)
        _tk.Label(manual_card, text="Manual Management", bg='#0A0A0A', fg='#9333ea',
                  font=("Segoe UI", 11, "bold"), anchor='w').pack(fill='x', padx=12, pady=(12, 6))
        _tk.Label(manual_card, 
                  text="Click the '📊 Excel' button in the main UI to open the Excel/CSV Manager. From there you can:",
                  bg='#0A0A0A', fg='#CCCCCC', font=("Segoe UI", 10), anchor='w', justify='left', wraplength=650).pack(fill='x', padx=12, pady=(0, 6))
        manual_features = [
            "• Load existing Excel/CSV files",
            "• View all modpacks and their addons",
            "• Edit addon details (name, version, notes)",
            "• Delete addons from modpacks",
            "• Add new addons to modpacks",
            "• Save changes back to the file",
        ]
        for feature in manual_features:
            _tk.Label(manual_card, text=feature, bg='#0A0A0A', fg='#CCCCCC', font=("Segoe UI", 10),
                      anchor='w', justify='left', wraplength=650).pack(fill='x', padx=12, pady=(0, 4))
        
        # File format
        format_card = _tk.Frame(org_inner, bg='#0A0A0A', relief='flat')
        format_card.pack(fill='x', pady=(0, 12), padx=5)
        _tk.Label(format_card, text="File Format", bg='#0A0A0A', fg='#9333ea',
                  font=("Segoe UI", 11, "bold"), anchor='w').pack(fill='x', padx=12, pady=(12, 6))
        _tk.Label(format_card, 
                  text="The system automatically chooses the best format based on your system:",
                  bg='#0A0A0A', fg='#CCCCCC', font=("Segoe UI", 10), anchor='w', justify='left', wraplength=650).pack(fill='x', padx=12, pady=(0, 6))
        format_info = [
            "• CSV format (default): Works without any dependencies, can be opened in Excel",
            "• Excel format (.xlsx): Requires openpyxl library, provides richer formatting",
            "• Both formats contain the same data and can be used interchangeably",
        ]
        for info in format_info:
            _tk.Label(format_card, text=info, bg='#0A0A0A', fg='#CCCCCC', font=("Segoe UI", 10),
                      anchor='w', justify='left', wraplength=650).pack(fill='x', padx=12, pady=(0, 4))
        _tk.Label(format_card, text="No installation required - CSV mode works out of the box!",
                  bg='#0A0A0A', fg='#9ca3af', font=("Segoe UI", 9), anchor='w', justify='left', wraplength=650).pack(fill='x', padx=12, pady=(8, 12))
        
        # Future features
        future_card = _tk.Frame(org_inner, bg='#0A0A0A', relief='flat')
        future_card.pack(fill='x', pady=(0, 12), padx=5)
        _tk.Label(future_card, text="Coming Soon", bg='#0A0A0A', fg='#9333ea',
                  font=("Segoe UI", 11, "bold"), anchor='w').pack(fill='x', padx=12, pady=(12, 6))
        future_features = [
            "• Automatic modpack updates from Excel/CSV changes",
            "• Add new addons to existing modpacks without full re-merge",
            "• Update addon versions within modpacks",
            "• Remove addons from modpacks safely",
            "• Full integration with both merge modes (all together vs by script version)",
        ]
        for feature in future_features:
            _tk.Label(future_card, text=feature, bg='#0A0A0A', fg='#CCCCCC', font=("Segoe UI", 10),
                      anchor='w', justify='left', wraplength=650).pack(fill='x', padx=12, pady=(0, 4))
        
        return section_frame

    def check_manifest(self, file_path):
        """Check if the manifest.json exists in the mcpack/mcaddon file."""
        with _zipfile.ZipFile(file_path, 'r') as zip_ref:
            return 'manifest.json' in zip_ref.namelist()

    def sanitize_filename(self, filename):
        """Sanitize the filename to make it safe for the filesystem."""
        return _re.sub(r'[^\w\-_\. ]', '_', filename)

    def process_files(self, files, output_dir, save_each_pack_as_mcpack=False):
        """Process the selected .mcpack and .mcaddon files using recursive extraction, then merge/pack them. Optionally, save each found pack as a .mcpack in the output directory."""
        packs_to_process = []
        for input_file in files:
            ext = _os.path.splitext(input_file)[1].lower()
            if ext in ('.mcpack', '.mcaddon', '.zip'):
                packs = recursive_extract_pack(input_file)
                packs_to_process.extend(packs)
        # Optionally save each found pack as a .mcpack
        if save_each_pack_as_mcpack:
            for pack_folder in packs_to_process:
                out_name = _os.path.basename(pack_folder.rstrip('/\\')) + ".mcpack"
                out_path = _os.path.join(output_dir, out_name)
                folder_to_mcpack(pack_folder, out_path)
        # Now pass the valid pack folders to the main merge/pack logic
        if packs_to_process:
            self._process_packs(packs_to_process, output_dir)
        else:
            _messagebox.showerror(_("msg.error"), _("error.no_packs_found"))

    def _rebuild_mcpacker_file_list(self):
        for w in self._mcpacker_file_list_inner.winfo_children():
            w.destroy()
        self._mcpacker_file_list_photo_refs.clear()
        self._mcpacker_file_list_selected.clear()
        for idx, (display_name, path, photo, full_photo) in enumerate(self._mcpacker_file_list_data):
            row = _tk.Frame(self._mcpacker_file_list_inner, bg='#0A0A0A', height=52)
            row.pack(fill='x', padx=4, pady=2)
            row.pack_propagate(False)
            if photo:
                self._mcpacker_file_list_photo_refs.append(photo)
                if full_photo:
                    self._mcpacker_file_list_photo_refs.append(full_photo)
                icon_lbl = _tk.Label(row, image=photo, bg='#0A0A0A')
            else:
                icon_lbl = _tk.Label(row, text='\u26fa', font=('Segoe UI', 20), bg='#0A0A0A', fg='#666666')
            icon_lbl.pack(side=_tk.LEFT, padx=(8, 10), pady=6)
            name_lbl = _tk.Label(row, text=display_name, bg='#0A0A0A', fg='#FFFFFF', font=('Segoe UI', 10), anchor='w')
            name_lbl.pack(side=_tk.LEFT, fill='x', expand=True, pady=6)
            for c in (row, icon_lbl, name_lbl):
                c.bind('<Button-1>', lambda e, i=idx: self._toggle_mcpacker_file_selection(i))
                if hasattr(self, '_mcpacker_wheel_handler'):
                    for _ev in ('<MouseWheel>', '<Button-4>', '<Button-5>'):
                        c.bind(_ev, self._mcpacker_wheel_handler)
            row._idx = idx
        self._mcpacker_file_list_canvas.configure(scrollregion=self._mcpacker_file_list_canvas.bbox('all'))

    def _toggle_mcpacker_file_selection(self, idx):
        if idx in self._mcpacker_file_list_selected:
            self._mcpacker_file_list_selected.discard(idx)
        else:
            self._mcpacker_file_list_selected.add(idx)
        for row in self._mcpacker_file_list_inner.winfo_children():
            if hasattr(row, '_idx'):
                sel = row._idx in self._mcpacker_file_list_selected
                bg = '#9333ea' if sel else '#0A0A0A'
                row.config(bg=bg)
                for c in row.winfo_children():
                    c.config(bg=bg)

    def select_files(self):
        """Open file dialog to select .mcpack and .mcaddon files."""
        file_paths = _filedialog.askopenfilenames(
            title=_("filedialog.select_mcpack_mcaddon"),
            filetypes=[("Minecraft Files", "*.mcpack *.mcaddon")]
        )
        for file_path in file_paths:
            display_name, photo, full_photo = self._get_pack_display_info(file_path)
            self._mcpacker_file_list_data.append((display_name, file_path, photo, full_photo))
            self._mcpacker_file_paths[display_name] = file_path
        self._mcpacker_files = [item[1] for item in self._mcpacker_file_list_data]
        self._rebuild_mcpacker_file_list()
        self._update_mcpacker_file_count()

    def remove_mcpacker_files(self):
        for index in sorted(self._mcpacker_file_list_selected, reverse=True):
            if 0 <= index < len(self._mcpacker_file_list_data):
                self._mcpacker_file_list_data.pop(index)
        self._mcpacker_file_paths = {}
        for display_name, path, *_ in self._mcpacker_file_list_data:
            self._mcpacker_file_paths[display_name] = path
        self._mcpacker_files = list(self._mcpacker_file_paths.values())
        self._rebuild_mcpacker_file_list()
        self._update_mcpacker_file_count()

    def _toggle_select_all_mcpacker(self):
        """Select all MCPACKER files if not all selected, otherwise deselect all."""
        all_indices = set(range(len(self._mcpacker_file_list_data)))
        if self._mcpacker_file_list_selected >= all_indices:
            self._mcpacker_file_list_selected.clear()
            self._mcpacker_btn_select_all.config(text="Select All")
        else:
            self._mcpacker_file_list_selected = all_indices.copy()
            self._mcpacker_btn_select_all.config(text="Deselect All")
        for row in self._mcpacker_file_list_inner.winfo_children():
            if hasattr(row, '_idx'):
                sel = row._idx in self._mcpacker_file_list_selected
                bg = '#9333ea' if sel else '#1a1a1a'
                row.config(bg=bg)
                for c in row.winfo_children():
                    c.config(bg=bg)

    def _update_mcpacker_file_count(self):
        """Update the file count label for MCPACKER."""
        count = len(self._mcpacker_files)
        self._mcpacker_file_count_label.config(text=_f("app.files_selected", n=count))
        if hasattr(self, '_mcpacker_btn_select_all'):
            if count > 0:
                self._mcpacker_btn_select_all.grid()
                all_sel = self._mcpacker_file_list_selected >= set(range(count))
                self._mcpacker_btn_select_all.config(text="Deselect All" if all_sel else "Select All")
            else:
                self._mcpacker_btn_select_all.grid_remove()

    def _reset_mcpacker_list(self):
        """Clear MCPACKER file list and output selection (called from main thread) after process completes."""
        self._mcpacker_files = []
        self._mcpacker_file_paths = {}
        self._mcpacker_file_list_data = []
        self._mcpacker_file_list_selected.clear()
        self._mcpacker_file_list_photo_refs.clear()
        self.output_dir_var.set("")
        self._rebuild_mcpacker_file_list()
        self._update_mcpacker_file_count()

    def select_output_directory(self):
        """Open file dialog to select the output directory."""
        directory = _filedialog.askdirectory(title=_("filedialog.select_output_dir"))
        self.output_dir_var.set(directory)

    def start_process(self):
        """Start processing the selected files."""
        files = self.files_var.get().split(',')
        output_dir = self.output_dir_var.get()
        
        if not files or not output_dir:
            _messagebox.showerror(_("msg.error"), _("process.select_files_and_output"))
            return
        
        self.process_files(files, output_dir)
        _messagebox.showinfo(_("msg.success"), _("process.completed"))
        
    def _generate_hwid(self):
        """Generate a hardware-based unique identifier."""
        if platform.system() == "Windows":
            # Try PowerShell Get-CimInstance (modern replacement for WMIC)
            try:
                ps_command = "Get-CimInstance -ClassName Win32_ComputerSystemProduct | Select-Object -ExpandProperty UUID"
                output = subprocess.check_output(
                    ["powershell", "-Command", ps_command],
                    stderr=subprocess.STDOUT,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
                ).strip()
                if output:
                    return output
            except Exception:
                pass
            # Try WMIC (legacy, may not work on newer Windows)
            try:
                output = subprocess.check_output(
                    ["wmic", "csproduct", "get", "uuid"],
                    stderr=subprocess.STDOUT,
                    text=True
                ).splitlines()
                uuid_value = next(
                    (line.strip() for line in output if line.strip() and line.strip().lower() != "uuid"),
                    None
                )
                if uuid_value:
                    return uuid_value
            except Exception:
                pass
            # Fallback if both methods fail
            return hashlib.md5(platform.node().encode()).hexdigest()
        elif platform.system() == "Linux":
            try:
                with open("/etc/machine-id", "r") as f:
                    return f.read().strip()
            except Exception as e:
                # Fallback if file read fails
                return hashlib.md5(platform.node().encode()).hexdigest()
        elif platform.system() == "Darwin":
            try:
                command = "system_profiler SPHardwareDataType | grep 'Hardware UUID'"
                uuid = subprocess.check_output(command, shell=True).decode().split(": ")[1].strip()
                return uuid
            except Exception as e:
                # Fallback if shell command fails
                return hashlib.md5(platform.node().encode()).hexdigest()
        else:
            return hashlib.md5(platform.node().encode()).hexdigest()

    def _update_progress(self, step, progress_percent, message):
        """Update the progress display with current step and message."""
        if hasattr(self, '_progress_step_label'):
            self._progress_step_label.config(text=message)
            self._progress['value'] = progress_percent
            self._root.update_idletasks()
            
            # Update step indicators
            if hasattr(self, '_step_labels') and 1 <= step <= 4:
                for i in range(4):
                    if i < step - 1:
                        # Completed steps
                        self._step_labels[i]['status'].config(text="✓", fg='#9333ea')
                        self._step_labels[i]['label'].config(fg='#FFFFFF')
                    elif i == step - 1:
                        # Current step
                        self._step_labels[i]['status'].config(text="→", fg='#9333ea')
                        self._step_labels[i]['label'].config(fg='#9333ea')
                    else:
                        # Pending steps
                        self._step_labels[i]['status'].config(text="○", fg='#666666')
                        self._step_labels[i]['label'].config(fg='#999999')
                # Mark all as complete if step 4 is done
                if step == 4:
                    for i in range(4):
                        self._step_labels[i]['status'].config(text="✓", fg='#9333ea')
                        self._step_labels[i]['label'].config(fg='#FFFFFF')

    def _reset_progress(self):
        """Reset progress display to initial state."""
        if hasattr(self, '_progress_step_label'):
            self._progress_step_label.config(text=_("app.ready_to_process"))
            self._progress['value'] = 0
            if hasattr(self, '_step_labels'):
                for step_info in self._step_labels:
                    step_info['status'].config(text="○", fg='#666666')
                    step_info['label'].config(fg='#999999')

    def _show_subpack_selection(self, file_name, subpack_options):
        """Show a themed subpack selection overlay that matches the tool's theme."""
        # ── Palette ──────────────────────────────────────────────────────────
        C_OVERLAY   = '#080a0e'
        C_CARD      = '#111318'
        C_CARD_ALT  = '#1c2030'
        C_LIST_BG   = '#0b0d14'
        C_BORDER    = '#3a4260'
        C_ACCENT    = '#9333ea'
        C_ACCENT_LT = '#c084fc'
        C_ACCENT_DK = '#6b21a8'
        C_SEL_BG    = '#7c3aed'   # bright violet — clearly visible on selection
        C_SEL_FG    = '#ffffff'
        C_FG        = '#f0f4ff'   # near-white for max readability
        C_FG_MUTED  = '#8892a4'
        C_FG_DIM    = '#b0bcd4'
        C_NUM_BG    = '#231d3a'
        C_NUM_FG    = '#c4b5fd'

        # Clear existing widgets in overlay
        for widget in self._subpack_overlay.winfo_children():
            widget.destroy()
        self._subpack_overlay.configure(bg=C_OVERLAY)

        selection_done  = _tk.BooleanVar(self._root, False)
        selected_index  = [None]

        # ── Outer wrapper (dims background visually) ─────────────────────────
        center_frame = _tk.Frame(self._subpack_overlay, bg=C_OVERLAY)
        center_frame.place(relx=0.5, rely=0.5, anchor='center')

        # Accent glow border (1-px purple outline)
        glow = _tk.Frame(center_frame, bg=C_ACCENT, bd=0)
        glow.pack()

        # Card shell — sized by content; children use consistent padx to keep width stable
        card = _tk.Frame(glow, bg=C_CARD, bd=0)
        card.pack(padx=1, pady=1)

        # Top accent stripe
        _tk.Frame(card, bg=C_ACCENT, height=4).pack(fill='x')

        # ── Header ───────────────────────────────────────────────────────────
        hdr = _tk.Frame(card, bg=C_CARD)
        hdr.pack(fill='x', padx=28, pady=(18, 0))

        # Title row
        title_row = _tk.Frame(hdr, bg=C_CARD)
        title_row.pack(fill='x')
        _tk.Label(title_row, text='📦', bg=C_CARD, fg=C_ACCENT_LT,
                  font=('Segoe UI', 17)).pack(side='left', padx=(0, 8))
        _tk.Label(title_row, text=_("subpack.title"), bg=C_CARD, fg=C_FG,
                  font=('Segoe UI', 15, 'bold')).pack(side='left')

        # Count badge
        count_txt = f'{len(subpack_options)} variant{"s" if len(subpack_options) != 1 else ""}'
        badge = _tk.Label(title_row, text=count_txt, bg=C_NUM_BG, fg=C_NUM_FG,
                          font=('Segoe UI', 8, 'bold'), padx=8, pady=2)
        badge.pack(side='left', padx=(12, 0))

        # File name (truncated)
        _short = file_name if len(file_name) <= 56 else file_name[:53] + '…'
        _tk.Label(hdr, text=_short, bg=C_CARD, fg=C_FG_MUTED,
                  font=('Segoe UI', 9), anchor='w').pack(fill='x', pady=(5, 0))

        # ── Divider ───────────────────────────────────────────────────────────
        _tk.Frame(card, bg=C_BORDER, height=1).pack(fill='x', padx=28, pady=(14, 0))

        # ── Body ─────────────────────────────────────────────────────────────
        body = _tk.Frame(card, bg=C_CARD)
        body.pack(fill='both', expand=True, padx=28, pady=(14, 0))

        _tk.Label(body, text=_("subpack.instruction"),
                  bg=C_CARD, fg=C_FG_DIM, font=('Segoe UI', 9),
                  anchor='w').pack(fill='x', pady=(0, 8))

        # List border
        lb_border = _tk.Frame(body, bg=C_BORDER, bd=0)
        lb_border.pack(fill='both', expand=True, pady=(0, 14))

        lb_inner = _tk.Frame(lb_border, bg=C_LIST_BG, bd=0)
        lb_inner.pack(fill='both', expand=True, padx=1, pady=1)
        lb_inner.configure(height=260)
        lb_inner.pack_propagate(False)

        sb = _tk.Scrollbar(lb_inner, orient='vertical',
                           bg=C_CARD_ALT, troughcolor=C_LIST_BG,
                           activebackground=C_BORDER, width=13, relief='flat')
        sb.pack(side='right', fill='y')

        listbox = _tk.Listbox(lb_inner,
                              bg=C_LIST_BG, fg=C_FG,
                              font=('Segoe UI', 12),
                              selectbackground=C_SEL_BG,
                              selectforeground=C_SEL_FG,
                              relief='flat', bd=0,
                              yscrollcommand=sb.set,
                              highlightthickness=0,
                              activestyle='none',
                              cursor='hand2',
                              borderwidth=0,
                              selectborderwidth=0)
        listbox.pack(side='left', fill='both', expand=True)
        sb.config(command=listbox.yview)

        # Populate — number + spacing + name for clear readability
        for i, option in enumerate(subpack_options):
            listbox.insert(_tk.END, f'    {i + 1:>2}.   {option}')

        if subpack_options:
            listbox.selection_set(0)
            listbox.see(0)

        # Keyboard hint
        hint_row = _tk.Frame(body, bg=C_CARD)
        hint_row.pack(fill='x', pady=(0, 2))
        _tk.Label(hint_row, text='↵ Enter to confirm  ·  Esc to cancel  ·  Double-click to select',
                  bg=C_CARD, fg=C_FG_MUTED, font=('Segoe UI', 8),
                  anchor='w').pack(side='left')

        # ── Divider ───────────────────────────────────────────────────────────
        _tk.Frame(card, bg=C_BORDER, height=1).pack(fill='x', padx=28, pady=(8, 0))

        # ── Buttons ───────────────────────────────────────────────────────────
        btn_row = _tk.Frame(card, bg=C_CARD)
        btn_row.pack(fill='x', padx=28, pady=(14, 24))

        # Select (primary)
        ok_btn = _tk.Button(btn_row, text='  \u2714   ' + _("subpack.select") + '  ',
                            command=lambda: None,   # assigned below
                            bg=C_ACCENT, fg='#ffffff',
                            font=('Segoe UI', 11, 'bold'),
                            relief='flat', bd=0, cursor='hand2',
                            activebackground=C_ACCENT_LT,
                            activeforeground='#ffffff',
                            padx=8, pady=10)
        ok_btn.pack(side='right', padx=(10, 0))

        # Cancel (secondary)
        cancel_btn = _tk.Button(btn_row, text='  ' + _("common.cancel") + '  ',
                                command=lambda: None,
                                bg=C_CARD_ALT, fg=C_FG_DIM,
                                font=('Segoe UI', 11),
                                relief='flat', bd=0, cursor='hand2',
                                activebackground=C_BORDER,
                                activeforeground=C_FG,
                                padx=8, pady=10)
        cancel_btn.pack(side='right')

        # ── Actions ───────────────────────────────────────────────────────────
        def on_ok(_event=None):
            sel = listbox.curselection()
            if sel:
                selected_index[0] = sel[0] + 1
            selection_done.set(True)
            self._subpack_overlay.grid_remove()

        def on_cancel(_event=None):
            selected_index[0] = None
            selection_done.set(True)
            self._subpack_overlay.grid_remove()

        ok_btn.configure(command=on_ok)
        cancel_btn.configure(command=on_cancel)
        listbox.bind('<Double-Button-1>', on_ok)
        listbox.bind('<Return>', on_ok)
        card.bind_all('<Escape>', on_cancel)

        # ── Show ──────────────────────────────────────────────────────────────
        self._subpack_overlay.grid()
        self._subpack_overlay.tkraise()
        listbox.focus_set()
        self._root.update()

        self._root.wait_variable(selection_done)
        try:
            card.unbind_all('<Escape>')
        except Exception:
            pass
        
        return selected_index[0]

    def _rebuild_autobe_file_list(self):
        """Rebuild the AutoBE file list display (icon + name rows) from _file_list_data."""
        for w in self._file_list_inner.winfo_children():
            w.destroy()
        self._file_list_photo_refs.clear()
        self._file_list_selected.clear()
        for idx, (display_name, path, photo, full_photo) in enumerate(self._file_list_data):
            row = _tk.Frame(self._file_list_inner, bg='#0A0A0A', height=52)
            row.pack(fill='x', padx=4, pady=2)
            row.pack_propagate(False)
            if photo:
                self._file_list_photo_refs.append(photo)
                if full_photo:
                    self._file_list_photo_refs.append(full_photo)
                icon_lbl = _tk.Label(row, image=photo, bg='#0A0A0A')
            else:
                icon_lbl = _tk.Label(row, text='\u26fa', font=('Segoe UI', 20), bg='#0A0A0A', fg='#666666')
            icon_lbl.pack(side=_tk.LEFT, padx=(8, 10), pady=6)
            name_lbl = _tk.Label(row, text=display_name, bg='#0A0A0A', fg='#FFFFFF', font=('Segoe UI', 10), anchor='w')
            name_lbl.pack(side=_tk.LEFT, fill='x', expand=True, pady=6)
            for c in (row, icon_lbl, name_lbl):
                c.bind('<Button-1>', lambda e, i=idx: self._toggle_autobe_file_selection(i))
                if hasattr(self, '_file_list_wheel_handler'):
                    for _ev in ('<MouseWheel>', '<Button-4>', '<Button-5>'):
                        c.bind(_ev, self._file_list_wheel_handler)
            row._idx = idx
        self._file_list_canvas.configure(scrollregion=self._file_list_canvas.bbox('all'))

    def _toggle_autobe_file_selection(self, idx):
        if idx in self._file_list_selected:
            self._file_list_selected.discard(idx)
        else:
            self._file_list_selected.add(idx)
        for row in self._file_list_inner.winfo_children():
            if hasattr(row, '_idx'):
                sel = row._idx in self._file_list_selected
                bg = '#9333ea' if sel else '#0A0A0A'
                row.config(bg=bg)
                for c in row.winfo_children():
                    c.config(bg=bg)

    def _add_files(self):
        _files = _filedialog.askopenfilenames(filetypes=[("McPack files", "*.mcpack")])
        mcpack_names = []
        for _file in _files:
            display_name, photo, full_photo = self._get_pack_display_info(_file)
            self._file_list_data.append((display_name, _file, photo, full_photo))
            self._file_paths[display_name] = _file
            mcpack_names.append(_os.path.basename(_file))
        self._files = [item[1] for item in self._file_list_data]
        self.mcpack_names = mcpack_names
        self._rebuild_autobe_file_list()
        self._update_file_count()

    def _remove_files(self):
        for _index in sorted(self._file_list_selected, reverse=True):
            if 0 <= _index < len(self._file_list_data):
                self._file_list_data.pop(_index)
        self._file_paths = {}
        for display_name, path, *_ in self._file_list_data:
            self._file_paths[display_name] = path
        self._files = [item[1] for item in self._file_list_data]
        self._rebuild_autobe_file_list()
        self._update_file_count()

    def _toggle_select_all_files(self):
        """Select all files if not all selected, otherwise deselect all."""
        all_indices = set(range(len(self._file_list_data)))
        if self._file_list_selected >= all_indices:
            # All already selected -> deselect all
            self._file_list_selected.clear()
            self._btn_select_all.config(text="Select All")
        else:
            # Select all
            self._file_list_selected = all_indices.copy()
            self._btn_select_all.config(text="Deselect All")
        for row in self._file_list_inner.winfo_children():
            if hasattr(row, '_idx'):
                sel = row._idx in self._file_list_selected
                bg = '#9333ea' if sel else '#0A0A0A'
                row.config(bg=bg)
                for c in row.winfo_children():
                    c.config(bg=bg)

    def _update_file_count(self):
        """Update the file count label for AutoBE section."""
        count = len(self._files)
        self._file_count_label.config(text=_f("app.files_selected", n=count))
        # Show/hide Select All button depending on whether any files are loaded
        if hasattr(self, '_btn_select_all'):
            if count > 0:
                self._btn_select_all.grid()
                # Sync label with current selection state
                all_selected = self._file_list_selected >= set(range(count))
                self._btn_select_all.config(text="Deselect All" if all_selected else "Select All")
            else:
                self._btn_select_all.grid_remove()
        # Update achievement status when files change
        self._check_achievement_compatibility()

    def _check_achievement_compatibility(self):
        """Check if any packs disable achievements and update the status button."""
        if not hasattr(self, '_btn_achievement_status'):
            return
        
        self._achievement_disabling_packs = []
        
        # If no files selected, show default status
        if not self._files:
            self._btn_achievement_status.config(text="✅ " + _("app.achievements_active"), bg='#10b981', activebackground='#059669')
            return
        
        # Check each pack for achievement-disabling features (behavior packs only; RPs don't disable achievements)
        for _file in self._files:
            manifest_data = self._get_manifest_data(_file)
            if not manifest_data:
                continue
            
            # Resource packs never disable achievements; only check behavior packs
            modules = manifest_data.get('modules') or []
            if isinstance(modules, list) and len(modules) > 0:
                first_type = modules[0].get('type') if isinstance(modules[0], dict) else None
                if first_type == 'resources':
                    continue  # Skip RP; it does not disable achievements
            
            pack_name = _os.path.basename(_file)
            disables_achievements = False
            
            # Check for script_eval capability (most common cause)
            if 'capabilities' in manifest_data:
                capabilities = manifest_data['capabilities']
                if isinstance(capabilities, list):
                    if 'script_eval' in capabilities or 'experimental_custom_syntax' in capabilities:
                        disables_achievements = True
            
            # Check for script modules (type: "script")
            if 'modules' in manifest_data:
                modules = manifest_data['modules']
                if isinstance(modules, list):
                    for module in modules:
                        if isinstance(module, dict) and module.get('type') == 'script':
                            disables_achievements = True
                            break
            
            # Check for experimental gameplay features in header
            if 'header' in manifest_data:
                header = manifest_data['header']
                if isinstance(header, dict):
                    # Check for experimental field
                    if header.get('experimental') is True:
                        disables_achievements = True
            
            if disables_achievements:
                self._achievement_disabling_packs.append(pack_name)
        
        # Update button appearance only (no hover tooltip; click opens overlay)
        if self._achievement_disabling_packs:
            self._btn_achievement_status.config(text="❌ " + _("achievements.disabled"), bg='#ef4444', activebackground='#dc2626')
        else:
            self._btn_achievement_status.config(text="✅ " + _("app.achievements_active"), bg='#10b981', activebackground='#059669')

    def _show_achievement_overlay(self):
        """Show in-app screen with packs that disable achievements vs packs that do not. Same layout as Script API overlay."""
        for widget in self._achievement_overlay.winfo_children():
            widget.destroy()
        
        self._achievement_overlay.grid_columnconfigure(0, weight=1)
        self._achievement_overlay.grid_rowconfigure(0, weight=1)
        
        main_container = _tk.Frame(self._achievement_overlay, bg='#0f1419')
        main_container.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        main_container.grid_columnconfigure(0, weight=1)
        main_container.grid_rowconfigure(0, weight=1)
        
        card_frame = _tk.Frame(main_container, bg='#1a1a1a', relief='flat', bd=0)
        card_frame.grid(row=0, column=0, sticky="nsew")
        card_frame.grid_columnconfigure(0, weight=1)
        card_frame.grid_rowconfigure(1, weight=1)
        
        border_frame = _tk.Frame(card_frame, bg='#9333ea', height=3)
        border_frame.grid(row=0, column=0, sticky="ew")
        
        inner_frame = _tk.Frame(card_frame, bg='#1a1a1a')
        inner_frame.grid(row=1, column=0, sticky="nsew", padx=40, pady=30)
        inner_frame.grid_columnconfigure(0, weight=1)
        inner_frame.grid_rowconfigure(1, weight=1)
        
        title_label = _tk.Label(inner_frame, text="🏆 " + _("achievements.overlay_title"),
                               bg='#1a1a1a', fg='#FFFFFF', font=('Segoe UI', 18, 'bold'))
        title_label.grid(row=0, column=0, pady=(0, 6), sticky="w")
        
        if not self._files:
            msg_label = _tk.Label(inner_frame, text=_("achievements.no_packs_msg"),
                                 bg='#1a1a1a', fg='#999999', font=('Segoe UI', 11), wraplength=1200, justify='left')
            msg_label.grid(row=1, column=0, pady=20, sticky="w")
        else:
            disabling_set = set(self._achievement_disabling_packs)
            ok_packs = []
            for f in self._files:
                name = _os.path.basename(f)
                if name in disabling_set:
                    continue
                manifest_data = self._get_manifest_data(f)
                if not manifest_data:
                    continue
                modules = manifest_data.get('modules') or []
                if isinstance(modules, list) and len(modules) > 0:
                    first_type = modules[0].get('type') if isinstance(modules[0], dict) else None
                    if first_type == 'resources':
                        continue
                ok_packs.append(name)
            ok_packs = sorted(ok_packs)
            disabling_packs = sorted(self._achievement_disabling_packs)
            
            canvas_container = _tk.Frame(inner_frame, bg='#1a1a1a')
            canvas_container.grid(row=1, column=0, sticky="nsew")
            canvas_container.grid_columnconfigure(0, weight=1)
            canvas_container.grid_rowconfigure(0, weight=1)
            
            canvas = _tk.Canvas(canvas_container, bg='#1a1a1a', highlightthickness=0)
            scrollable_frame = _tk.Frame(canvas, bg='#1a1a1a')
            
            def update_scroll_region(event=None):
                canvas.update_idletasks()
                canvas.configure(scrollregion=canvas.bbox("all"))
            
            def _on_mousewheel(event):
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            
            def _scroll_bind_enter(event):
                canvas_container.bind_all("<MouseWheel>", _on_mousewheel)
            
            def _scroll_bind_leave(event):
                canvas_container.unbind_all("<MouseWheel>")
            
            scrollable_frame.bind("<Configure>", update_scroll_region)
            canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas.find_all()[0], width=e.width) if canvas.find_all() else None)
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas_container.bind("<Enter>", _scroll_bind_enter)
            canvas_container.bind("<Leave>", _scroll_bind_leave)
            canvas.bind("<Enter>", _scroll_bind_enter)
            scrollable_frame.bind("<Enter>", _scroll_bind_enter)
            
            row_num = 0
            
            dis_header = _tk.Frame(scrollable_frame, bg='#ef4444', height=42)
            dis_header.grid(row=row_num, column=0, sticky="ew", padx=0, pady=(0, 0))
            dis_header.grid_columnconfigure(0, weight=1)
            d_count = len(disabling_packs)
            _tk.Label(dis_header, text=f"  ❌ Packs that DISABLE achievements  ·  {d_count} pack{'s' if d_count != 1 else ''}  ",
                     bg='#ef4444', fg='#FFFFFF', font=('Segoe UI', 12, 'bold'), anchor='w').grid(row=0, column=0, padx=20, pady=10, sticky="w")
            row_num += 1
            for pack_name in disabling_packs:
                display_name = (pack_name[:80] + "…") if len(pack_name) > 80 else pack_name
                row_f = _tk.Frame(scrollable_frame, bg='#1a1a1a', height=36)
                row_f.grid(row=row_num, column=0, sticky="ew", padx=20, pady=2)
                row_f.grid_columnconfigure(0, weight=1)
                _tk.Label(row_f, text=display_name, bg='#1a1a1a', fg='#fca5a5', font=('Segoe UI', 11), anchor='w').grid(row=0, column=0, padx=24, pady=8, sticky="w")
                row_num += 1
            row_num += 6
            
            ok_header = _tk.Frame(scrollable_frame, bg='#10b981', height=42)
            ok_header.grid(row=row_num, column=0, sticky="ew", padx=0, pady=(0, 0))
            ok_header.grid_columnconfigure(0, weight=1)
            o_count = len(ok_packs)
            _tk.Label(ok_header, text=f"  ✅ Packs that do NOT disable achievements  ·  {o_count} pack{'s' if o_count != 1 else ''}  ",
                     bg='#10b981', fg='#FFFFFF', font=('Segoe UI', 12, 'bold'), anchor='w').grid(row=0, column=0, padx=20, pady=10, sticky="w")
            row_num += 1
            for pack_name in ok_packs:
                display_name = (pack_name[:80] + "…") if len(pack_name) > 80 else pack_name
                row_f = _tk.Frame(scrollable_frame, bg='#1a1a1a', height=36)
                row_f.grid(row=row_num, column=0, sticky="ew", padx=20, pady=2)
                row_f.grid_columnconfigure(0, weight=1)
                _tk.Label(row_f, text=display_name, bg='#1a1a1a', fg='#6ee7b7', font=('Segoe UI', 11), anchor='w').grid(row=0, column=0, padx=24, pady=8, sticky="w")
                row_num += 1
            
            scrollable_frame.grid_columnconfigure(0, weight=1)
            canvas.grid(row=0, column=0, sticky="nsew")
            self._root.after(100, update_scroll_region)
        
        def on_close():
            self._achievement_overlay.grid_remove()
        
        button_frame = _tk.Frame(inner_frame, bg='#1a1a1a')
        button_frame.grid(row=2, column=0, pady=(15, 0))
        close_btn = _tk.Button(button_frame, text=_("common.close"), command=on_close,
                              bg='#9333ea', fg='#FFFFFF', font=('Segoe UI', 11, 'bold'),
                              relief='flat', cursor='hand2', activebackground='#a855f7',
                              padx=30, pady=10)
        close_btn.pack()
        
        self._achievement_overlay.grid()
        self._achievement_overlay.lift()

    def _detect_com_mojang(self):
        """Return the first existing com.mojang path from known locations."""
        candidates = [
            _os.path.join(_os.environ.get('APPDATA', ''), 'Minecraft Bedrock', 'Users', 'Shared', 'games', 'com.mojang'),
            _os.path.expandvars(r'%LOCALAPPDATA%\Packages\Microsoft.MinecraftUWP_8wekyb3d8bbwe\LocalState\games\com.mojang'),
            _os.path.expandvars(r'%LOCALAPPDATA%\Packages\Microsoft.MinecraftWindowsBeta_8wekyb3d8bbwe\LocalState\games\com.mojang'),
        ]
        for c in candidates:
            if _os.path.isdir(c):
                return c
        return ''

    def _toggle_mc_import_path(self):
        """Enable or disable the com.mojang path entry based on the checkbox state."""
        enabled = self._auto_import_var.get()
        state = 'normal' if enabled else 'disabled'
        fg_entry = '#FFFFFF' if enabled else '#888888'
        fg_btn   = '#FFFFFF' if enabled else '#888888'
        bg_btn   = '#9333ea' if enabled else '#374151'
        try:
            entry = getattr(self, '_entry_mc_path', None)
            if entry and entry.winfo_exists():
                entry.config(state=state, fg=fg_entry)
        except Exception:
            pass
        try:
            btn = getattr(self, '_btn_mc_browse', None)
            if btn and btn.winfo_exists():
                btn.config(state=state, fg=fg_btn, bg=bg_btn)
        except Exception:
            pass

    def _browse_mc_path(self):
        """Let the user browse to a custom com.mojang directory."""
        path = _filedialog.askdirectory(title="Select com.mojang folder")
        if path:
            self._mc_path_var.set(path)

    def _import_to_minecraft(self, base_dir):
        """Unzip the merged behavior_pack.mcpack / resource_pack.mcpack into com.mojang."""
        mc_path = self._mc_path_var.get().strip()
        if not mc_path or not _os.path.isdir(mc_path):
            _logging.warning(f"Auto-import skipped — com.mojang path not found: {mc_path!r}")
            self._root.after(0, lambda p=mc_path: self._show_import_panel([], error=f"com.mojang folder not found:\n{p}"))
            return
        bp_dest_root = _os.path.join(mc_path, 'behavior_packs')
        rp_dest_root = _os.path.join(mc_path, 'resource_packs')
        _os.makedirs(bp_dest_root, exist_ok=True)
        _os.makedirs(rp_dest_root, exist_ok=True)
        imported = []
        # Collect all output dirs (base_dir itself + version subdirs)
        dirs_to_check = [base_dir] + [_os.path.join(base_dir, d) for d in _os.listdir(base_dir)
                                      if _os.path.isdir(_os.path.join(base_dir, d))]
        for out_dir in dirs_to_check:
            tag = _os.path.basename(out_dir) if out_dir != base_dir else 'merged'
            pack_name = f'AutoBE_{tag}'
            for mcpack, dest_root, kind in [
                ('behavior_pack.mcpack',  bp_dest_root, 'BP'),
                ('resource_pack.mcpack',  rp_dest_root, 'RP'),
            ]:
                src = _os.path.join(out_dir, mcpack)
                if not _os.path.isfile(src):
                    continue
                dest = _os.path.join(dest_root, f'{pack_name}_{kind}')
                if _os.path.isdir(dest):
                    _shutil.rmtree(dest)
                _os.makedirs(dest, exist_ok=True)
                try:
                    with _zipfile.ZipFile(src, 'r') as _z:
                        _z.extractall(dest)
                    imported.append(f'{pack_name}_{kind}')
                    _logging.info(f"Auto-imported {mcpack} → {dest}")
                except Exception as _e:
                    _logging.error(f"Auto-import failed for {src}: {_e}")
        if imported:
            self._root.after(0, lambda i=imported: self._show_import_panel(i))
        else:
            _logging.warning("Auto-import: no merged packs found to import.")

    def _show_import_panel(self, imported, error=None):
        """Show an in-window styled card for auto-import results (replaces popup)."""
        # Remove any previous import panel
        existing = getattr(self, '_import_panel_overlay', None)
        if existing:
            try:
                existing.destroy()
            except Exception:
                pass

        is_error = bool(error)
        accent   = '#ef4444' if is_error else '#9333ea'

        # Full-window dim overlay
        overlay = _tk.Frame(self._root, bg='#0a0a0a')
        overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        self._import_panel_overlay = overlay

        # Centered card
        card = _tk.Frame(overlay, bg='#1a1a1a', relief='flat', bd=0)
        card.place(relx=0.5, rely=0.5, anchor='center')

        # Top accent border
        _tk.Frame(card, bg=accent, height=3).pack(fill='x')

        inner = _tk.Frame(card, bg='#1a1a1a')
        inner.pack(fill='both', expand=True, padx=28, pady=24)

        # Icon + title row
        icon  = '✗' if is_error else '✓'
        title = 'Import Failed' if is_error else f'Imported {len(imported)} pack(s) to Minecraft Bedrock'
        title_row = _tk.Frame(inner, bg='#1a1a1a')
        title_row.pack(fill='x', pady=(0, 14))
        _tk.Label(title_row, text=icon, bg='#1a1a1a', fg=accent,
                  font=('Segoe UI', 20, 'bold')).pack(side='left', padx=(0, 10))
        _tk.Label(title_row, text=title, bg='#1a1a1a', fg='#FFFFFF',
                  font=('Segoe UI', 13, 'bold'), wraplength=380, justify='left').pack(side='left', fill='x', expand=True)

        if not is_error:
            # Compact BP/RP color legend
            leg = _tk.Frame(inner, bg='#111111', highlightthickness=1, highlightbackground='#2d2d2d')
            leg.pack(fill='x', pady=(0, 10))
            _tk.Label(leg, text='  Color key:', bg='#111111', fg='#999999',
                      font=('Segoe UI', 9, 'bold')).pack(side='left', padx=(8, 4), pady=5)
            for dot_col, dot_lbl in [('#a78bfa', 'Behavior Pack'), ('#34d399', 'Resource Pack')]:
                sw = _tk.Frame(leg, bg=dot_col, width=10, height=10)
                sw.pack(side='left', padx=(6, 2))
                sw.pack_propagate(False)
                _tk.Label(leg, text=dot_lbl, bg='#111111', fg='#d1d5db',
                          font=('Segoe UI', 9)).pack(side='left', padx=(0, 12), pady=5)

        if is_error:
            _tk.Label(inner, text=error, bg='#1a1a1a', fg='#999999',
                      font=('Segoe UI', 10), wraplength=400, justify='left').pack(anchor='w', pady=(0, 16))
        else:
            # Scrollable pack list
            list_outer = _tk.Frame(inner, bg='#111111', highlightthickness=1, highlightbackground='#2d2d2d')
            list_outer.pack(fill='x', pady=(0, 16))
            scroll = _tk.Scrollbar(list_outer, orient='vertical', bg='#1a1a1a',
                                   troughcolor='#111111', activebackground='#9333ea')
            scroll.pack(side='right', fill='y')
            listbox = _tk.Listbox(list_outer, bg='#111111', fg='#d1d5db',
                                  font=('Segoe UI', 10), relief='flat', bd=0,
                                  selectbackground='#9333ea', selectforeground='#FFFFFF',
                                  activestyle='none', highlightthickness=0,
                                  height=min(len(imported), 10),
                                  yscrollcommand=scroll.set)
            listbox.pack(side='left', fill='both', expand=True, padx=10, pady=8)
            scroll.config(command=listbox.yview)
            for pack in imported:
                # colour BP/RP differently
                listbox.insert(_tk.END, f'  {pack}')
                tag_col = '#a78bfa' if pack.endswith('_BP') else '#34d399'
                listbox.itemconfig(_tk.END, fg=tag_col)

        # Dismiss button
        def _dismiss():
            try:
                overlay.destroy()
            except Exception:
                pass
        btn_frame = _tk.Frame(inner, bg='#1a1a1a')
        btn_frame.pack(fill='x')
        _tk.Button(btn_frame, text='Done', command=_dismiss,
                   bg=accent, fg='#FFFFFF', font=('Segoe UI', 10, 'bold'),
                   relief='flat', cursor='hand2', padx=24, pady=6,
                   activebackground='#7e22ce', activeforeground='#FFFFFF').pack(side='right')

        overlay.bind('<Button-1>', lambda e: _dismiss() if e.widget is overlay else None)

    def _select_output_dir(self):
        _dir_name = _filedialog.askdirectory()
        if _dir_name:
            self._output_dir_var.set(_dir_name)
            self._out_dir = _dir_name

    def _collect_merged_output_dirs(self, base_dir):
        """Return list of directories that contain behavior_pack.mcpack (this merge output and any version subdirs)."""
        dirs = []
        if _os.path.isfile(_os.path.join(base_dir, "behavior_pack.mcpack")):
            dirs.append(base_dir)
        for name in _os.listdir(base_dir):
            sub = _os.path.join(base_dir, name)
            if _os.path.isdir(sub) and _os.path.isfile(_os.path.join(sub, "behavior_pack.mcpack")):
                dirs.append(sub)
        return dirs

    def _show_customize_merged_pack_dialog(self, current_dir, remaining_dirs=None):
        """Show one popup to name/describe/icon/author this merged pack only. When Apply or Skip, close and show next if remaining_dirs."""
        remaining_dirs = remaining_dirs or []
        pack_label = _os.path.basename(current_dir)
        if not pack_label:
            pack_label = _os.path.basename(_os.path.dirname(current_dir)) or "merged pack"
        title = _("customize.title") if _("customize.title") != "customize.title" else "Name your merged pack"
        dlg = _tk.Toplevel(self._root)
        self._apply_window_icon(dlg)
        dlg.title(title + " — " + pack_label)
        dlg.configure(bg="#1a1a1a")
        dlg.transient(self._root)
        dlg.geometry("440x420")
        dlg.resizable(True, True)
        try:
            sw, sh = self._root.winfo_screenwidth(), self._root.winfo_screenheight()
            dlg.maxsize(sw, sh)
            dlg.update_idletasks()
            w, h = dlg.winfo_reqwidth(), dlg.winfo_reqheight()
            x = max(0, (sw - w) // 2)
            y = max(0, (sh - h) // 2)
            dlg.geometry(f"440x420+{x}+{y}")
        except Exception:
            pass
        main = _tk.Frame(dlg, bg="#1a1a1a", padx=24, pady=24)
        main.pack(fill="both", expand=True)
        main.grid_columnconfigure(1, weight=1)
        subtitle_lbl = _tk.Label(main, text=_f("customize.this_pack", pack=pack_label) if _("customize.this_pack") != "customize.this_pack" else "This merged pack only: " + pack_label, bg="#1a1a1a", fg="#9333ea", font=("Segoe UI", 10), wraplength=380)
        subtitle_lbl.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 12))
        def _on_customize_resize(event):
            try:
                if subtitle_lbl.winfo_exists():
                    subtitle_lbl.configure(wraplength=max(200, event.width - 80))
            except Exception:
                pass
        dlg.bind("<Configure>", _on_customize_resize)
        default_name = _("customize.default_name") if _("customize.default_name") != "customize.default_name" else "My Merged Pack"
        default_desc = _("customize.default_desc") if _("customize.default_desc") != "customize.default_desc" else "Merged with AutoBE"
        _tk.Label(main, text=_("customize.name"), bg="#1a1a1a", fg="#E5E7EB", font=("Segoe UI", 11, "bold")).grid(row=1, column=0, sticky="w", pady=(0, 6))
        name_var = _tk.StringVar(value=default_name)
        _tk.Entry(main, textvariable=name_var, bg="#0A0A0A", fg="#FFFFFF", font=("Segoe UI", 11), insertbackground="#a855f7", relief="flat").grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 16))
        _tk.Label(main, text=_("customize.description"), bg="#1a1a1a", fg="#E5E7EB", font=("Segoe UI", 11, "bold")).grid(row=3, column=0, sticky="w", pady=(0, 6))
        desc_var = _tk.StringVar(value=default_desc)
        _tk.Entry(main, textvariable=desc_var, bg="#0A0A0A", fg="#FFFFFF", font=("Segoe UI", 11), insertbackground="#a855f7", relief="flat").grid(row=4, column=0, columnspan=2, sticky="ew", pady=(0, 16))
        _tk.Label(main, text=_("customize.icon"), bg="#1a1a1a", fg="#E5E7EB", font=("Segoe UI", 11, "bold")).grid(row=5, column=0, sticky="w", pady=(0, 6))
        icon_path_var = _tk.StringVar(value="")
        icon_label = _tk.Label(main, text=_("customize.no_icon") if _("customize.no_icon") != "customize.no_icon" else "None", bg="#1a1a1a", fg="#999999", font=("Segoe UI", 10), anchor="w")
        icon_label.grid(row=6, column=0, columnspan=2, sticky="w", pady=(0, 16))

        def pick_icon():
            path = _filedialog.askopenfilename(title=_("customize.pick_icon") if _("customize.pick_icon") != "customize.pick_icon" else "Pick pack icon", filetypes=[("Images", "*.png *.jpg *.jpeg"), ("PNG", "*.png"), ("JPEG", "*.jpg *.jpeg"), ("All", "*")])
            if path:
                icon_path_var.set(path)
                icon_label.config(text=_os.path.basename(path), fg="#E5E7EB")

        _tk.Button(main, text=_("customize.browse_icon") if _("customize.browse_icon") != "customize.browse_icon" else "Browse...", command=pick_icon, bg="#3a3a3a", fg="#FFFFFF", font=("Segoe UI", 10), relief="flat", cursor="hand2", activebackground="#9333ea").grid(row=6, column=1, sticky="e", pady=(0, 16))
        _tk.Label(main, text=_("customize.author"), bg="#1a1a1a", fg="#E5E7EB", font=("Segoe UI", 11, "bold")).grid(row=7, column=0, sticky="w", pady=(0, 6))
        author_var = _tk.StringVar(value="")
        _tk.Entry(main, textvariable=author_var, bg="#0A0A0A", fg="#FFFFFF", font=("Segoe UI", 11), insertbackground="#a855f7", relief="flat").grid(row=8, column=0, columnspan=2, sticky="ew", pady=(0, 16))

        def apply_and_next():
            name = (name_var.get() or "").strip() or default_name
            desc = (desc_var.get() or "").strip() or default_desc
            icon_path = (icon_path_var.get() or "").strip()
            if not icon_path or not _os.path.isfile(icon_path):
                icon_path = None
            author = (author_var.get() or "").strip()
            bp_path = _os.path.join(current_dir, "behavior_pack.mcpack")
            rp_path = _os.path.join(current_dir, "resource_pack.mcpack")
            if _os.path.isfile(bp_path):
                self._update_mcpack_metadata(bp_path, name, desc, icon_path, author=author)
            if _os.path.isfile(rp_path):
                self._update_mcpack_metadata(rp_path, name, desc, icon_path, author=author)
            dlg.destroy()
            if remaining_dirs:
                self._root.after(50, lambda: self._show_customize_merged_pack_dialog(remaining_dirs[0], remaining_dirs[1:]))
            else:
                _messagebox.showinfo(_("customize.done_title") or "Done", _("customize.done_msg") if _("customize.done_msg") != "customize.done_msg" else "Pack name, description, icon, and author updated.")

        def skip_and_next():
            dlg.destroy()
            if remaining_dirs:
                self._root.after(50, lambda: self._show_customize_merged_pack_dialog(remaining_dirs[0], remaining_dirs[1:]))

        btn_frame = _tk.Frame(main, bg="#1a1a1a")
        btn_frame.grid(row=9, column=0, columnspan=2, pady=(20, 0))
        skip_text = _("customize.skip") if _("customize.skip") != "customize.skip" else "Skip"
        apply_text = _("customize.apply") if _("customize.apply") != "customize.apply" else "Apply"
        _tk.Button(btn_frame, text=skip_text, command=skip_and_next, bg="#3a3a3a", fg="#FFFFFF", font=("Segoe UI", 11), relief="flat", cursor="hand2", activebackground="#555", padx=20, pady=10).pack(side="left", padx=(0, 12))
        _tk.Button(btn_frame, text=apply_text, command=apply_and_next, bg="#9333ea", fg="#FFFFFF", font=("Segoe UI", 11, "bold"), relief="flat", cursor="hand2", activebackground="#a855f7", padx=20, pady=10).pack(side="left")

    def _load_merge_manifest(self, folder):
        """Load _autobe_merge_manifest.json from folder or its subdirs. Return (manifest_dict, manifest_folder) or (None, None)."""
        path = _os.path.join(folder, "_autobe_merge_manifest.json")
        if _os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return _json.load(f), folder
            except Exception:
                pass
        for name in _os.listdir(folder):
            sub = _os.path.join(folder, name)
            if _os.path.isdir(sub):
                path = _os.path.join(sub, "_autobe_merge_manifest.json")
                if _os.path.isfile(path):
                    try:
                        with open(path, "r", encoding="utf-8") as f:
                            return _json.load(f), sub
                    except Exception:
                        pass
        return None, None

    def _show_linked_packs_dialog(self, forced_output_dir=None):
        """Show dialog listing addons in the current merge; allow removing one and re-merging without it. If forced_output_dir is set, use it instead of UI output path."""
        out_dir = (forced_output_dir or "").strip() if forced_output_dir else None
        if not out_dir or not _os.path.isdir(out_dir):
            out_dir = (self._output_dir_var.get() or "").strip()
        if not out_dir or not _os.path.isdir(out_dir):
            out_dir = _filedialog.askdirectory(title=_("linked.select_output") if _("linked.select_output") != "linked.select_output" else "Select merged output folder")
        if not out_dir:
            return
        manifest_data, manifest_folder = self._load_merge_manifest(out_dir)
        if not manifest_data:
            _messagebox.showinfo(
                _("linked.no_manifest_title") if _("linked.no_manifest_title") != "linked.no_manifest_title" else "Linked packs",
                _("linked.no_manifest_msg") if _("linked.no_manifest_msg") != "linked.no_manifest_msg" else "No merge manifest found in this folder. Run a merge first, then use Linked packs to view or remove addons."
            )
            return
        source_packs = manifest_data.get("source_packs") or []
        output_dir = manifest_data.get("output_dir") or manifest_folder
        if not source_packs:
            _messagebox.showinfo(_("linked.no_manifest_title") or "Linked packs", _("linked.no_packs_in_manifest") or "No source packs listed in manifest.")
            return
        dlg = _tk.Toplevel(self._root)
        self._apply_window_icon(dlg)
        dlg.title(_("linked.title") if _("linked.title") != "linked.title" else "Linked packs")
        dlg.configure(bg="#1a1a1a")
        dlg.transient(self._root)
        dlg.geometry("420x380")
        dlg.resizable(True, True)
        try:
            sw, sh = self._root.winfo_screenwidth(), self._root.winfo_screenheight()
            dlg.maxsize(sw, sh)
            dlg.update_idletasks()
            w, h = dlg.winfo_reqwidth(), dlg.winfo_reqheight()
            x = max(0, (sw - w) // 2)
            y = max(0, (sh - h) // 2)
            dlg.geometry(f"420x380+{x}+{y}")
        except Exception:
            pass
        main = _tk.Frame(dlg, bg="#1a1a1a", padx=20, pady=20)
        main.pack(fill="both", expand=True)
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(1, weight=1)
        linked_desc_lbl = _tk.Label(main, text=_("linked.desc") if _("linked.desc") != "linked.desc" else "Addons in this merge. Remove one to re-merge without it.", bg="#1a1a1a", fg="#E5E7EB", font=("Segoe UI", 11), wraplength=380, justify="left")
        linked_desc_lbl.grid(row=0, column=0, sticky="w", pady=(0, 12))
        def _on_linked_resize(event):
            try:
                if linked_desc_lbl.winfo_exists():
                    linked_desc_lbl.configure(wraplength=max(200, event.width - 80))
            except Exception:
                pass
        dlg.bind("<Configure>", _on_linked_resize)
        list_frame = _tk.Frame(main, bg="#0A0A0A", highlightthickness=1, highlightbackground="#404040")
        list_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 12))
        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(0, weight=1)
        canvas = _tk.Canvas(list_frame, bg="#0A0A0A", highlightthickness=0)
        canvas.grid(row=0, column=0, sticky="nsew")
        inner = _tk.Frame(canvas, bg="#0A0A0A")
        inner.grid_columnconfigure(0, weight=1)
        canvas_window = canvas.create_window(0, 0, window=inner, anchor="nw")
        def _on_configure(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(canvas_window, width=e.width)
        inner.bind("<Configure>", _on_configure)
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_window, width=e.width))
        def _on_wheel(e):
            canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        def _enter(e):
            canvas.bind_all("<MouseWheel>", _on_wheel)
        def _leave(e):
            try:
                canvas.unbind_all("<MouseWheel>")
            except Exception:
                pass
        canvas.bind("<Enter>", _enter)
        canvas.bind("<Leave>", _leave)
        inner.bind("<Enter>", _enter)
        inner.bind("<Leave>", _leave)
        remove_btn_vars = []
        for i, path in enumerate(source_packs):
            row = _tk.Frame(inner, bg="#1a1a1a", height=40)
            row.grid(row=i, column=0, sticky="ew", padx=8, pady=4)
            row.grid_columnconfigure(0, weight=1)
            name = _os.path.basename(path)
            if len(name) > 45:
                name = name[:42] + "…"
            _tk.Label(row, text=name, bg="#1a1a1a", fg="#FFFFFF", font=("Segoe UI", 10), anchor="w").grid(row=0, column=0, sticky="w", padx=8, pady=8)
            remove_text = _("linked.remove") if _("linked.remove") != "linked.remove" else "Remove"
            btn = _tk.Button(row, text=remove_text, command=lambda p=path: _do_remove(p), bg="#7f1d1d", fg="#FFFFFF", font=("Segoe UI", 9), relief="flat", cursor="hand2", activebackground="#991b1b")
            btn.grid(row=0, column=1, padx=8, pady=6)
            remove_btn_vars.append((path, btn))

        def _do_remove(path_to_remove):
            confirm_msg = _("linked.remove_confirm") if _("linked.remove_confirm") != "linked.remove_confirm" else "Remove this addon from the merge? The pack will be re-merged without it (output will be overwritten)."
            if not _messagebox.askyesno(_("linked.remove_confirm_title") or "Remove addon", confirm_msg):
                return
            remaining = [p for p in source_packs if p != path_to_remove]
            existing = [p for p in remaining if _os.path.isfile(p)]
            if not existing:
                _messagebox.showerror(_("msg.error"), _("linked.cannot_remove_only") if _("linked.cannot_remove_only") != "linked.cannot_remove_only" else "Need at least one pack remaining.")
                return
            if len(existing) < len(remaining):
                _messagebox.showwarning(_("linked.missing_title") or "Some files missing", _("linked.missing_msg") if _("linked.missing_msg") != "linked.missing_msg" else "Some original packs were moved or deleted; only existing paths will be used.")
            dlg.destroy()
            self._files = existing
            self._output_dir_var.set(output_dir)
            self._out_dir = output_dir
            self._file_list_data = [(_os.path.basename(p), p, None, None) for p in existing]
            self._file_paths = {_os.path.basename(p): p for p in existing}
            self._rebuild_autobe_file_list()
            self._file_count_label.config(text=_f("app.files_selected", n=len(existing)))
            self._process_and_create_manifest()

        _tk.Button(main, text=_("common.close"), command=dlg.destroy, bg="#3a3a3a", fg="#FFFFFF", font=("Segoe UI", 11), relief="flat", cursor="hand2", activebackground="#9333ea", padx=20, pady=10).grid(row=2, column=0, pady=(0, 0))

    def _update_mcpack_metadata(self, mcpack_path, name, description, icon_path=None, author=None):
        """Update manifest name/description/author and optionally pack_icon in an existing .mcpack zip."""
        if not _os.path.isfile(mcpack_path):
            return
        try:
            with _zipfile.ZipFile(mcpack_path, 'r') as zf:
                namelist = zf.namelist()
                manifest_name = None
                for n in namelist:
                    if n.lower().endswith('manifest.json'):
                        manifest_name = n
                        break
                if not manifest_name:
                    return
                manifest_bytes = zf.read(manifest_name)
            try:
                manifest = _json.loads(manifest_bytes.decode('utf-8'))
            except Exception:
                return
            header = manifest.get('header') or {}
            header['name'] = name
            header['description'] = description
            manifest['header'] = header
            modules = manifest.get('modules') or []
            if modules and isinstance(modules[0], dict):
                modules[0]['description'] = description
            manifest['modules'] = modules
            if author is not None:
                meta = manifest.get('metadata') or {}
                manifest['metadata'] = meta
                meta['authors'] = [author] if author.strip() else []
            new_manifest_bytes = _json.dumps(manifest, indent=2).encode('utf-8')
            icon_ext = None
            if icon_path and _os.path.isfile(icon_path):
                icon_ext = _os.path.splitext(icon_path)[1].lower()
                if icon_ext not in ('.png', '.jpg', '.jpeg'):
                    icon_ext = '.png'
            tmp_path = mcpack_path + '.autobe_tmp'
            with _zipfile.ZipFile(tmp_path, 'w', _zipfile.ZIP_DEFLATED) as zout:
                with _zipfile.ZipFile(mcpack_path, 'r') as zf:
                    for item in zf.namelist():
                        if item == manifest_name:
                            zout.writestr(item, new_manifest_bytes)
                        elif icon_ext and item.lower().endswith(('pack_icon.png', 'pack_icon.jpg', 'pack_icon.jpeg')):
                            continue
                        else:
                            zout.writestr(item, zf.read(item))
                if icon_path and _os.path.isfile(icon_path):
                    with open(icon_path, 'rb') as f:
                        icon_data = f.read()
                    icon_basename = 'pack_icon.png' if icon_ext in ('.png',) or not icon_ext else 'pack_icon' + icon_ext
                    prefix = _os.path.dirname(manifest_name)
                    out_icon_name = (_os.path.join(prefix, icon_basename).replace('\\', '/')) if prefix else icon_basename
                    zout.writestr(out_icon_name, icon_data)
            _os.replace(tmp_path, mcpack_path)
        except Exception as e:
            _logging.warning(f"Could not update mcpack metadata {mcpack_path}: {e}")

    def _process_and_create_manifest(self):
        if not self._files:
            _messagebox.showerror(_("msg.error"), _("process.select_mcpacks_only"))
            _logging.error("No .mcpack files selected")
            return
        if not self._out_dir:
            _messagebox.showerror(_("msg.error"), _("process.select_output"))
            _logging.error("No output directory selected")
            return

        if not self._validate_files():
            return

        # Disable start button during processing
        self._btn_start.config(state='disabled')
        
        # Run processing in a separate thread to prevent UI freezing
        def process_thread():
            try:
                self._root.after(0, lambda: self._reset_progress())
                self._root.after(0, lambda: self._update_progress(0, 0, "Initializing process..."))
                _logging.info("=== AutoBE merge started ===")
                _logging.info(f"  Files selected: {len(self._files)}")
                _logging.info(f"  Output dir: {self._out_dir}")
                merge_by_version = getattr(self, "merge_by_version_var", None) and self.merge_by_version_var.get()
                _logging.info(f"  Merge by version: {merge_by_version}")
                customize_base = self._out_dir
                if merge_by_version:
                    _logging.info("Grouping files by script API version...")
                    groups = self._group_files_by_script_api_version(self._files)
                    if not groups:
                        _logging.error("No valid mcpack groups found — aborting.")
                        self._root.after(0, lambda: _messagebox.showerror(_("msg.error"), _("process.no_valid_mcpacks")))
                        return
                    _logging.info(f"  Groups found: { {k: len(v) for k, v in groups.items()} }")
                    # Separate groups into: packs needing Preview Minecraft vs
                    # packs that only need the Beta APIs toggle in stable Bedrock.
                    _preview_groups   = {k: v for k, v in groups.items()
                                         if 'preview' in k.lower() and k != 'none'}
                    _beta_alpha_groups = {k: v for k, v in groups.items()
                                          if any(s in k.lower() for s in ('beta', 'alpha', 'rc'))
                                          and 'preview' not in k.lower() and k != 'none'}
                    _has_stable = any(
                        k != 'none' and not any(s in k.lower() for s in ('beta', 'alpha', 'rc', 'preview'))
                        for k in groups)

                    if _preview_groups or _beta_alpha_groups:
                        _notice_lines = []

                        if _preview_groups:
                            _notice_lines += [
                                "Some of your addons require the PREVIEW version of",
                                "Minecraft Bedrock (the separate Preview app / channel).",
                                "They will NOT work in stable Bedrock.",
                                "",
                                "Addons that require Minecraft Preview:",
                            ]
                            for _pk, _pv in _preview_groups.items():
                                _notice_lines.append(f"  Script API: {_pk.replace('_', '.')}")
                                for _pf in _pv:
                                    _notice_lines.append(f"    \u2022 {_os.path.basename(_pf)}")
                            _notice_lines.append("")

                        if _beta_alpha_groups:
                            if _preview_groups:
                                _notice_lines += [
                                    "─" * 52,
                                    "",
                                ]
                            _multi = len(groups) > 1
                            _notice_lines += [
                                "Some of your addons use Experimental Script APIs",
                                "(versions ending in -beta or -alpha in their manifest).",
                                "",
                                "These work fine in STABLE Minecraft Bedrock —",
                                "just enable  \"Beta APIs\"  in your world's Experiments",
                                "before applying the packs.",
                            ]
                            if _multi:
                                _notice_lines += [
                                    "",
                                    "AutoBE places each API version in its own output",
                                    "subfolder. Apply ALL subfolders to the same world",
                                    "with Beta APIs ON.",
                                ]
                            _notice_lines += [
                                "",
                                "Addons that need the Beta APIs toggle:",
                            ]
                            for _bk, _bv in _beta_alpha_groups.items():
                                _notice_lines.append(f"  Script API: {_bk.replace('_', '.')}")
                                for _bf in _bv:
                                    _notice_lines.append(f"    \u2022 {_os.path.basename(_bf)}")
                            _notice_lines += [
                                "",
                                "How to enable: Edit World \u2192 Experiments \u2192 Beta APIs \u2192 ON.",
                                "Without it those addons' scripts will not run.",
                            ]

                        _notice_text = "\n".join(_notice_lines)
                        _has_preview_only = bool(_preview_groups) and not bool(_beta_alpha_groups)
                        _beta_done = threading.Event()
                        def _show_beta_warn(_bt=_notice_text, _prev=_has_preview_only):
                            try:
                                _win = _tk.Toplevel(self._root)
                                if _prev:
                                    _win.title("Preview Version Required")
                                    _hdr = "\u26a0  Minecraft Preview Required"
                                    _sub = "These addons require the separate Minecraft Preview app — they won't run in stable Bedrock."
                                elif _preview_groups:
                                    _win.title("Script API Notice")
                                    _hdr = "\u26a0  Preview + Beta API Addons Detected"
                                    _sub = "See details below for which addons need Preview and which only need the Beta APIs toggle."
                                else:
                                    _win.title("Beta APIs Required")
                                    _hdr = "⚠ Beta APIs Required"
                                    _sub = "Some addons use experimental features. Enable Beta APIs in your world settings before applying these packs."
                                _win.configure(bg='#1a1a2e')
                                _win.resizable(False, False)
                                _win.grab_set()
                                _win.lift()
                                
                                # Main container with padding
                                _container = _tk.Frame(_win, bg='#1a1a2e')
                                _container.pack(padx=32, pady=32, fill='both', expand=True)
                                
                                # Header with icon
                                _tk.Label(_container, text=_hdr,
                                          bg='#1a1a2e', fg='#f97316',
                                          font=("Segoe UI", 14, "bold")).pack(pady=(0, 12))
                                
                                # Subtitle with better spacing
                                _tk.Label(_container, text=_sub,
                                          bg='#1a1a2e', fg='#cbd5e1',
                                          font=("Segoe UI", 10), wraplength=500, justify='center').pack(pady=(0, 20))
                                
                                # Info box with border
                                _info_frame = _tk.Frame(_container, bg='#16213e', relief='solid', borderwidth=1)
                                _info_frame.pack(fill='both', expand=True, pady=(0, 20))
                                
                                _txt = _tk.Text(_info_frame, bg='#16213e', fg='#e2e8f0',
                                                font=("Consolas", 9), relief='flat',
                                                width=58, height=12, wrap='word',
                                                padx=12, pady=12)
                                _txt.insert('1.0', _bt)
                                _txt.configure(state='disabled')
                                _txt.pack(fill='both', expand=True, padx=1, pady=1)
                                
                                # Modern button with hover effect
                                _btn = _tk.Button(_container, text="Continue",
                                                   bg='#f97316', fg='#ffffff',
                                                   font=("Segoe UI", 10, "bold"), relief='flat',
                                                   padx=24, pady=10, cursor='hand2',
                                                   activebackground='#ea580c', activeforeground='#ffffff',
                                                   command=lambda: (_win.destroy(), _beta_done.set()))
                                _btn.pack(pady=(0, 0))
                                _win.protocol("WM_DELETE_WINDOW",
                                              lambda: (_win.destroy(), _beta_done.set()))
                            except Exception:
                                _beta_done.set()
                        self._root.after(0, _show_beta_warn)
                        _beta_done.wait()
                    original_out = self._out_dir
                    customize_base = original_out
                    # Store original files for Discord merge log (all groups combined)
                    original_files_all = list(self._files)
                    for folder_key, group_files in sorted(groups.items(), key=lambda x: (x[0] != 'none', x[0])):
                        _logging.info(f"  Processing group '{folder_key}' ({len(group_files)} files)...")
                        self._files = list(group_files)
                        self._out_dir = _os.path.join(original_out, folder_key)
                        _os.makedirs(self._out_dir, exist_ok=True)
                        self._start_process()
                        _logging.info(f"  Group '{folder_key}' done.")
                        _bp_mcpack = _os.path.join(self._out_dir, 'behavior_pack.mcpack')
                        _rp_mcpack = _os.path.join(self._out_dir, 'resource_pack.mcpack')
                    # Unify player.json across all groups so every RP has the same
                    # comprehensive player entity (animations + variables from all groups).
                    try:
                        self._unify_cross_group_player_json(original_out)
                    except Exception:
                        pass
                    # Unify player animation / animation-controller / render-controller files
                    # across all groups.  Play-as-Link lands in the 'none' group with 35 custom
                    # player animations; without this step Bedrock only honours the highest-priority
                    # RP's player.animation.json, silently discarding all the other groups' files.
                    try:
                        self._unify_cross_group_player_anims(original_out)
                    except Exception as _e:
                        _logging.error(f"[_unify_cross_group_player_anims] Failed: {_e}", exc_info=True)
                    # Unify terrain_texture.json / item_texture.json / blocks.json across all
                    # groups so custom block texture registrations from one group's RP (e.g.
                    # QB Furniture's warped_planks entry in 2_x RP) are present in every
                    # group's RP.  Without this, Bedrock may fail to resolve texture IDs for
                    # blocks whose BP is in a lower-priority group, showing them as dirt.
                    try:
                        self._unify_cross_group_atlas_files(original_out)
                    except Exception:
                        pass
                    # Unify hud_screen.json / _ui_defs.json across all groups so every RP
                    # carries the full set of HUD patches (e.g. temperature + mqps patches
                    # survive alongside Paraglider's dominant 150 KB hud_screen).
                    try:
                        self._unify_cross_group_hud_files(original_out)
                    except Exception:
                        pass
                    # Bake the merged root hud_screen.json into every subpack variant.
                    # Subpacks like SWAILA's position variants (topleft / topright / …) each
                    # carry their own hud_screen.json that REPLACES the root when selected,
                    # silently discarding mqps / temperature / Paraglider HUD changes.  This
                    # step merges the complete root hud_screen into each subpack so all HUD
                    # elements survive regardless of which position the user picks.
                    try:
                        self._merge_subpack_hud_files(original_out)
                    except Exception:
                        pass
                    # Send Discord merge log with ALL selected addons (not just current group)
                    try:
                        self._send_discord_merge_log(original_files_all)
                    except Exception as _e:
                        _logging.warning(f"Could not send Discord merge log: {_e}")
                    self._root.after(0, lambda: self._update_progress(4, 100, "All steps completed successfully! ✓"))
                    if getattr(self, '_auto_import_var', None) and self._auto_import_var.get():
                        self._import_to_minecraft(original_out)
                else:
                    _logging.info("Starting single-group merge...")
                    self._start_process()
                    _logging.info("Single-group merge done.")
                    _bp_mcpack_sg = _os.path.join(self._out_dir, 'behavior_pack.mcpack')
                    _rp_mcpack_sg = _os.path.join(self._out_dir, 'resource_pack.mcpack')
                    # Send Discord merge log with all selected addons (single-group case)
                    try:
                        self._send_discord_merge_log(self._files)
                    except Exception as _e:
                        _logging.warning(f"Could not send Discord merge log: {_e}")
                    self._root.after(0, lambda: self._update_progress(4, 100, "All steps completed successfully! ✓"))
                    if getattr(self, '_auto_import_var', None) and self._auto_import_var.get():
                        self._import_to_minecraft(self._out_dir)
                # Reset memory and clear the list on main thread
                self._root.after(0, lambda: self._reset_file_list())
                if getattr(self, "customize_pack_after_merge_var", None) and self.customize_pack_after_merge_var.get() and customize_base and _os.path.isdir(customize_base):
                    _dirs = self._collect_merged_output_dirs(customize_base)
                    if _dirs:
                        self._root.after(100, lambda: self._show_customize_merged_pack_dialog(_dirs[0], _dirs[1:]))
                if getattr(self, "show_linked_packs_after_merge_var", None) and self.show_linked_packs_after_merge_var.get() and customize_base and _os.path.isdir(customize_base):
                    self._root.after(600, lambda b=customize_base: self._show_linked_packs_dialog(forced_output_dir=b))
                # Excel organization after merge
                if getattr(self, "modpack_organization_var", None) and self.modpack_organization_var.get() and _EXCEL_MANAGER:
                    # Use original_files_all for script version merge, self._files for single group
                    files_to_use = original_files_all if groups else self._files
                    self._root.after(1000, lambda: self._handle_excel_organization(customize_base, files_to_use))
            except Exception as _e:
                log_error(_e)
                _logging.error("An error occurred during the process", exc_info=True)
                self._root.after(0, lambda: _messagebox.showerror(_("msg.error"), _f("process.an_error_occurred", error=_e)))
            finally:
                # Re-enable start button
                self._root.after(0, lambda: self._btn_start.config(state='normal'))
                # Always clean up any _modified.mcpack temp files — handles cancel, crash, early exit
                for _mf in getattr(self, '_pending_cleanup_mcpacks', []):
                    try:
                        if _os.path.exists(_mf):
                            _os.remove(_mf)
                    except Exception:
                        pass
                self._pending_cleanup_mcpacks = []
        
        threading.Thread(target=process_thread, daemon=True).start()
    
    def _handle_excel_organization(self, output_dir: str, source_files: list):
        """Handle Excel/CSV organization after merge - prompt for modpack name and create Excel/CSV sheet."""
        if not _EXCEL_MANAGER:
            _logging.warning("Excel/CSV functionality not available")
            return
        
        if not source_files:
            _logging.warning("No source files provided for Excel organization")
            return
        
        _logging.info(f"Opening Excel organization dialog with {len(source_files)} files")
        
        # Create dialog to get modpack name
        dialog = _tk.Toplevel(self._root)
        dialog.title("Modpack Organization")
        dialog.configure(bg='#1a1a1a')
        dialog.transient(self._root)
        dialog.grab_set()
        dialog.attributes('-topmost', True)  # Force dialog to be on top
        
        # Main container with padding
        main_frame = _tk.Frame(dialog, bg='#1a1a1a')
        main_frame.pack(fill='both', expand=True, padx=30, pady=30)
        
        # Title
        _tk.Label(main_frame, text="Modpack Organization", bg='#1a1a1a', fg='#FFFFFF',
                 font=("Segoe UI", 16, "bold")).pack(pady=(0, 15))
        
        # Description
        _tk.Label(main_frame, text="Name your modpack to organize addons in Excel/CSV", bg='#1a1a1a', fg='#CCCCCC',
                 font=("Segoe UI", 10)).pack(pady=(0, 20))
        
        # Modpack name input
        _tk.Label(main_frame, text="Modpack Name:", bg='#1a1a1a', fg='#FFFFFF',
                 font=("Segoe UI", 11)).pack(pady=(0, 5), anchor='w')
        
        name_var = _tk.StringVar()
        name_entry = _tk.Entry(main_frame, textvariable=name_var, width=45, bg='#0A0A0A', fg='#FFFFFF',
                              font=("Segoe UI", 11), insertbackground='#9333ea', relief='flat',
                              highlightthickness=1, highlightbackground='#1a1a1a', highlightcolor='#9333ea')
        name_entry.pack(pady=(0, 20), fill='x')
        name_entry.focus()
        
        # Version inputs
        version_frame = _tk.Frame(main_frame, bg='#1a1a1a')
        version_frame.pack(pady=(0, 20), fill='x')
        
        _tk.Label(version_frame, text="Min Version:", bg='#1a1a1a', fg='#FFFFFF',
                 font=("Segoe UI", 10)).grid(row=0, column=0, padx=(0, 10), pady=5, sticky='w')
        min_var = _tk.StringVar(value="1.21.0")
        _tk.Entry(version_frame, textvariable=min_var, width=20, bg='#0A0A0A', fg='#FFFFFF',
                 font=("Segoe UI", 10), relief='flat').grid(row=0, column=1, pady=5, sticky='w')
        
        _tk.Label(version_frame, text="Max Version:", bg='#1a1a1a', fg='#FFFFFF',
                 font=("Segoe UI", 10)).grid(row=1, column=0, padx=(0, 10), pady=5, sticky='w')
        max_var = _tk.StringVar(value="1.21.90")
        _tk.Entry(version_frame, textvariable=max_var, width=20, bg='#0A0A0A', fg='#FFFFFF',
                 font=("Segoe UI", 10), relief='flat').grid(row=1, column=1, pady=5, sticky='w')
        
        # Buttons
        button_frame = _tk.Frame(main_frame, bg='#1a1a1a')
        button_frame.pack(pady=(10, 0))
        
        def create_excel():
            modpack_name = name_var.get().strip()
            if not modpack_name:
                _messagebox.showerror("Error", "Please enter a modpack name")
                return
            
            try:
                # Extract addon info from source files
                addons = []
                for file_path in source_files:
                    addon_name = _os.path.basename(file_path)
                    # Try to get version from manifest
                    version = "Unknown"
                    try:
                        manifest = self._get_manifest_data(file_path)
                        if manifest and 'header' in manifest:
                            version = manifest['header'].get('version', 'Unknown')
                    except:
                        pass
                    
                    addons.append({
                        "name": addon_name,
                        "path": file_path,
                        "version": version,
                        "min_version": min_var.get(),
                        "max_version": max_var.get(),
                        "status": "Active",
                        "notes": ""
                    })
                
                # Create Excel sheet
                _EXCEL_MANAGER.create_new_workbook()
                _EXCEL_MANAGER.add_modpack_sheet(
                    modpack_name,
                    addons,
                    min_version=min_var.get(),
                    max_version=max_var.get()
                )
                
                # Save Excel/CSV file
                extension = ".csv" if _EXCEL_MANAGER.csv_mode else ".xlsx"
                excel_path = _os.path.join(output_dir, f"{modpack_name}_config{extension}")
                _EXCEL_MANAGER.save_workbook(excel_path)
                
                _messagebox.showinfo("Success", f"Modpack configuration saved to:\n{excel_path}")
                dialog.destroy()
                
            except Exception as e:
                _logging.error(f"Error creating Excel/CSV file: {e}")
                _messagebox.showerror("Error", f"Failed to create Excel/CSV file:\n{e}")
        
        def cancel():
            dialog.destroy()
        
        _tk.Button(button_frame, text="Create Excel/CSV", command=create_excel, bg='#9333ea', fg='#FFFFFF',
                  font=("Segoe UI", 11, "bold"), relief='flat', cursor='hand2', activebackground='#a855f7',
                  padx=20, pady=8).pack(side='left', padx=(0, 10))
        
        _tk.Button(button_frame, text="Cancel", command=cancel, bg='#1a1a1a', fg='#FFFFFF',
                  font=("Segoe UI", 11), relief='flat', cursor='hand2', activebackground='#2d2d2d',
                  padx=20, pady=8).pack(side='left')
        
        # Center dialog after all content is packed
        dialog.update_idletasks()
        width = dialog.winfo_reqwidth()
        height = dialog.winfo_reqheight()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")
        dialog.minsize(width, height)
    
    def _show_excel_manager(self):
        """Show Excel/CSV manager dialog for manual organization of modpacks."""
        if not _EXCEL_MANAGER:
            _messagebox.showerror("Error", "Excel/CSV functionality is not available")
            return
        
        dialog = _tk.Toplevel(self._root)
        dialog.title("Excel/CSV Modpack Manager")
        dialog.geometry("900x600")
        dialog.configure(bg='#1a1a1a')
        dialog.transient(self._root)
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (900 // 2)
        y = (dialog.winfo_screenheight() // 2) - (600 // 2)
        dialog.geometry(f"900x600+{x}+{y}")
        
        # Title
        _tk.Label(dialog, text="📊 Excel/CSV Modpack Manager", bg='#1a1a1a', fg='#FFFFFF',
                 font=("Segoe UI", 16, "bold")).pack(pady=(20, 10))
        
        # Description
        _tk.Label(dialog, text="Load Excel/CSV files to manage your modpacks manually", bg='#1a1a1a', fg='#CCCCCC',
                 font=("Segoe UI", 10)).pack(pady=(0, 20))
        
        # Main content frame
        content_frame = _tk.Frame(dialog, bg='#1a1a1a')
        content_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_rowconfigure(1, weight=1)
        
        # File selection frame
        file_frame = _tk.Frame(content_frame, bg='#1a1a1a')
        file_frame.grid(row=0, column=0, sticky='ew', pady=(0, 10))
        
        _tk.Label(file_frame, text="Excel/CSV File:", bg='#1a1a1a', fg='#FFFFFF',
                 font=("Segoe UI", 11)).pack(side='left', padx=(0, 10))
        
        excel_path_var = _tk.StringVar()
        excel_entry = _tk.Entry(file_frame, textvariable=excel_path_var, width=50, bg='#0A0A0A', fg='#FFFFFF',
                              font=("Segoe UI", 10), relief='flat')
        excel_entry.pack(side='left', padx=(0, 10))
        
        def browse_excel():
            file_path = _filedialog.askopenfilename(
                title="Select Excel/CSV File",
                filetypes=[("Excel/CSV Files", "*.xlsx;*.csv"), ("Excel Files", "*.xlsx"), ("CSV Files", "*.csv"), ("All Files", "*.*")]
            )
            if file_path:
                excel_path_var.set(file_path)
                load_excel_file(file_path)
        
        _tk.Button(file_frame, text="Browse", command=browse_excel, bg='#9333ea', fg='#FFFFFF',
                  font=("Segoe UI", 10), relief='flat', cursor='hand2').pack(side='left', padx=(0, 10))
        
        def create_new_excel():
            _EXCEL_MANAGER.create_new_workbook()
            _messagebox.showinfo("Success", "New Excel workbook created. Save it to continue.")
            save_excel_file()
        
        _tk.Button(file_frame, text="New", command=create_new_excel, bg='#10b981', fg='#FFFFFF',
                  font=("Segoe UI", 10), relief='flat', cursor='hand2').pack(side='left')
        
        # Modpack list frame
        list_frame = _tk.LabelFrame(content_frame, text="Modpacks", bg='#1a1a1a', fg='#FFFFFF',
                                    font=("Segoe UI", 11, "bold"))
        list_frame.grid(row=1, column=0, sticky='nsew')
        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(0, weight=1)
        
        # Listbox with scrollbar
        listbox_frame = _tk.Frame(list_frame, bg='#1a1a1a')
        listbox_frame.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)
        
        modpack_listbox = _tk.Listbox(listbox_frame, bg='#0A0A0A', fg='#FFFFFF', font=("Segoe UI", 10),
                                     selectmode='single', relief='flat', highlightthickness=0)
        modpack_listbox.pack(side='left', fill='both', expand=True)
        
        scrollbar = _tk.Scrollbar(listbox_frame, orient='vertical', command=modpack_listbox.yview)
        scrollbar.pack(side='right', fill='y')
        modpack_listbox.config(yscrollcommand=scrollbar.set)
        
        # Current modpack info
        info_frame = _tk.Frame(list_frame, bg='#1a1a1a')
        info_frame.grid(row=1, column=0, sticky='ew', padx=10, pady=(0, 10))
        
        info_label = _tk.Label(info_frame, text="No modpack selected", bg='#1a1a1a', fg='#CCCCCC',
                              font=("Segoe UI", 10))
        info_label.pack()
        
        # Buttons frame
        button_frame = _tk.Frame(dialog, bg='#1a1a1a')
        button_frame.pack(pady=(0, 20))
        
        def load_excel_file(file_path):
            try:
                configs = _EXCEL_MANAGER.load_from_excel(file_path)
                modpack_listbox.delete(0, _tk.END)
                for modpack_name in configs.keys():
                    modpack_listbox.insert(_tk.END, modpack_name)
                info_label.config(text=f"Loaded {len(configs)} modpack(s)")
            except Exception as e:
                _messagebox.showerror("Error", f"Failed to load Excel file:\n{e}")
        
        def save_excel_file():
            if _EXCEL_MANAGER.current_file:
                try:
                    _EXCEL_MANAGER.save_workbook(_EXCEL_MANAGER.current_file)
                    _messagebox.showinfo("Success", "Excel/CSV file saved successfully")
                except Exception as e:
                    _messagebox.showerror("Error", f"Failed to save Excel/CSV file:\n{e}")
            else:
                file_path = _filedialog.asksaveasfilename(
                    title="Save Excel/CSV File",
                    defaultextension=".csv" if _EXCEL_MANAGER.csv_mode else ".xlsx",
                    filetypes=[("Excel/CSV Files", "*.xlsx;*.csv"), ("Excel Files", "*.xlsx"), ("CSV Files", "*.csv"), ("All Files", "*.*")]
                )
                if file_path:
                    try:
                        _EXCEL_MANAGER.save_workbook(file_path)
                        excel_path_var.set(file_path)
                        _messagebox.showinfo("Success", "Excel/CSV file saved successfully")
                    except Exception as e:
                        _messagebox.showerror("Error", f"Failed to save Excel/CSV file:\n{e}")
        
        def edit_selected_modpack():
            selection = modpack_listbox.curselection()
            if not selection:
                _messagebox.showwarning("Warning", "Please select a modpack to edit")
                return
            
            modpack_name = modpack_listbox.get(selection[0])
            # Open edit dialog for selected modpack
            self._edit_modpack_dialog(dialog, modpack_name)
        
        def delete_selected_modpack():
            selection = modpack_listbox.curselection()
            if not selection:
                _messagebox.showwarning("Warning", "Please select a modpack to delete")
                return
            
            modpack_name = modpack_listbox.get(selection[0])
            if _messagebox.askyesno("Confirm", f"Delete modpack '{modpack_name}'?"):
                try:
                    sheet_name = _EXCEL_MANAGER._sanitize_sheet_name(modpack_name)
                    if sheet_name in _EXCEL_MANAGER.workbook.sheetnames:
                        _EXCEL_MANAGER.workbook.remove(_EXCEL_MANAGER.workbook[sheet_name])
                        modpack_listbox.delete(selection[0])
                        info_label.config(text=f"Deleted modpack '{modpack_name}'")
                except Exception as e:
                    _messagebox.showerror("Error", f"Failed to delete modpack:\n{e}")
        
        _tk.Button(button_frame, text="Load", command=lambda: load_excel_file(excel_path_var.get()), bg='#9333ea', fg='#FFFFFF',
                  font=("Segoe UI", 11), relief='flat', cursor='hand2', padx=15, pady=8).pack(side='left', padx=(0, 5))
        
        _tk.Button(button_frame, text="Save", command=save_excel_file, bg='#9333ea', fg='#FFFFFF',
                  font=("Segoe UI", 11), relief='flat', cursor='hand2', padx=15, pady=8).pack(side='left', padx=(0, 5))
        
        _tk.Button(button_frame, text="Edit", command=edit_selected_modpack, bg='#10b981', fg='#FFFFFF',
                  font=("Segoe UI", 11), relief='flat', cursor='hand2', padx=15, pady=8).pack(side='left', padx=(0, 5))
        
        _tk.Button(button_frame, text="Delete", command=delete_selected_modpack, bg='#ef4444', fg='#FFFFFF',
                  font=("Segoe UI", 11), relief='flat', cursor='hand2', padx=15, pady=8).pack(side='left', padx=(0, 5))
        
        def remerge_from_excel():
            selection = modpack_listbox.curselection()
            if not selection:
                _messagebox.showwarning("Warning", "Please select a modpack to re-merge")
                return
            
            modpack_name = modpack_listbox.get(selection[0])
            self._remerge_from_excel_dialog(dialog, modpack_name, excel_path_var.get())
        
        _tk.Button(button_frame, text="🔄 Re-merge", command=remerge_from_excel, bg='#f59e0b', fg='#FFFFFF',
                  font=("Segoe UI", 11), relief='flat', cursor='hand2', padx=15, pady=8).pack(side='left', padx=(0, 5))
        
        _tk.Button(button_frame, text="Close", command=dialog.destroy, bg='#1a1a1a', fg='#FFFFFF',
                  font=("Segoe UI", 11), relief='flat', cursor='hand2', padx=15, pady=8).pack(side='left')
    
    def _edit_modpack_dialog(self, parent_dialog, modpack_name):
        """Open dialog to edit a specific modpack's addons."""
        sheet_name = _EXCEL_MANAGER._sanitize_sheet_name(modpack_name)
        if sheet_name not in _EXCEL_MANAGER.workbook.sheetnames:
            _messagebox.showerror("Error", f"Modpack '{modpack_name}' not found")
            return
        
        sheet = _EXCEL_MANAGER.workbook[sheet_name]
        modpack_config = _EXCEL_MANAGER._parse_modpack_sheet(sheet)
        
        dialog = _tk.Toplevel(parent_dialog)
        dialog.title(f"Edit {modpack_name}")
        dialog.geometry("800x500")
        dialog.configure(bg='#1a1a1a')
        dialog.transient(parent_dialog)
        dialog.grab_set()
        
        # Title
        _tk.Label(dialog, text=f"📦 {modpack_name}", bg='#1a1a1a', fg='#FFFFFF',
                 font=("Segoe UI", 14, "bold")).pack(pady=(15, 10))
        
        # Addon list frame
        list_frame = _tk.LabelFrame(dialog, text="Addons", bg='#1a1a1a', fg='#FFFFFF',
                                    font=("Segoe UI", 11, "bold"))
        list_frame.pack(fill='both', expand=True, padx=15, pady=(0, 10))
        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(0, weight=1)
        
        # Treeview for addon list
        from tkinter import ttk
        tree_frame = _tk.Frame(list_frame, bg='#1a1a1a')
        tree_frame.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)
        
        columns = ("name", "version", "min_version", "max_version", "status")
        tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=15)
        tree.heading("name", text="Addon Name")
        tree.heading("version", text="Version")
        tree.heading("min_version", text="Min Ver")
        tree.heading("max_version", text="Max Ver")
        tree.heading("status", text="Status")
        
        tree.column("name", width=200)
        tree.column("version", width=100)
        tree.column("min_version", width=80)
        tree.column("max_version", width=80)
        tree.column("status", width=80)
        
        tree.pack(side='left', fill='both', expand=True)
        
        # Scrollbar
        tree_scroll = _tk.Scrollbar(tree_frame, orient='vertical', command=tree.yview)
        tree_scroll.pack(side='right', fill='y')
        tree.config(yscrollcommand=tree_scroll.set)
        
        # Populate tree
        for addon in modpack_config["addons"]:
            tree.insert('', 'end', values=(
                addon["name"],
                addon["version"],
                addon["min_version"],
                addon["max_version"],
                addon["status"]
            ))
        
        # Buttons
        button_frame = _tk.Frame(dialog, bg='#1a1a1a')
        button_frame.pack(pady=(0, 15))
        
        def add_addon():
            # Simple dialog to add addon
            add_dialog = _tk.Toplevel(dialog)
            add_dialog.title("Add Addon")
            add_dialog.geometry("400x300")
            add_dialog.configure(bg='#1a1a1a')
            add_dialog.transient(dialog)
            add_dialog.grab_set()
            
            _tk.Label(add_dialog, text="Addon Name:", bg='#1a1a1a', fg='#FFFFFF',
                     font=("Segoe UI", 10)).pack(pady=(10, 5))
            name_var = _tk.StringVar()
            _tk.Entry(add_dialog, textvariable=name_var, width=40, bg='#0A0A0A', fg='#FFFFFF').pack(pady=5)
            
            _tk.Label(add_dialog, text="Version:", bg='#1a1a1a', fg='#FFFFFF',
                     font=("Segoe UI", 10)).pack(pady=(10, 5))
            version_var = _tk.StringVar(value="1.0.0")
            _tk.Entry(add_dialog, textvariable=version_var, width=40, bg='#0A0A0A', fg='#FFFFFF').pack(pady=5)
            
            def confirm_add():
                new_addon = {
                    "name": name_var.get(),
                    "path": "",
                    "version": version_var.get(),
                    "min_version": modpack_config.get("min_version", "1.21.0"),
                    "max_version": modpack_config.get("max_version", "1.21.90"),
                    "status": "Active",
                    "notes": ""
                }
                modpack_config["addons"].append(new_addon)
                tree.insert('', 'end', values=(new_addon["name"], new_addon["version"], 
                                                new_addon["min_version"], new_addon["max_version"], new_addon["status"]))
                add_dialog.destroy()
            
            _tk.Button(add_dialog, text="Add", command=confirm_add, bg='#9333ea', fg='#FFFFFF',
                      font=("Segoe UI", 10), relief='flat').pack(pady=10)
        
        def remove_addon():
            selection = tree.selection()
            if not selection:
                _messagebox.showwarning("Warning", "Please select an addon to remove")
                return
            if _messagebox.askyesno("Confirm", "Remove selected addon?"):
                item = tree.selection()[0]
                index = tree.index(item)
                del modpack_config["addons"][index]
                tree.delete(item)
        
        def save_changes():
            # Update the sheet with new data
            _EXCEL_MANAGER.workbook.remove(sheet)
            _EXCEL_MANAGER.add_modpack_sheet(
                modpack_name,
                modpack_config["addons"],
                min_version=modpack_config.get("min_version", "1.21.0"),
                max_version=modpack_config.get("max_version", "1.21.90")
            )
            _messagebox.showinfo("Success", "Changes saved to workbook")
            dialog.destroy()
        
        _tk.Button(button_frame, text="Add Addon", command=add_addon, bg='#10b981', fg='#FFFFFF',
                  font=("Segoe UI", 10), relief='flat', cursor='hand2', padx=12, pady=6).pack(side='left', padx=(0, 5))
        
        _tk.Button(button_frame, text="Remove", command=remove_addon, bg='#ef4444', fg='#FFFFFF',
                  font=("Segoe UI", 10), relief='flat', cursor='hand2', padx=12, pady=6).pack(side='left', padx=(0, 5))
        
        _tk.Button(button_frame, text="Save Changes", command=save_changes, bg='#9333ea', fg='#FFFFFF',
                  font=("Segoe UI", 10), relief='flat', cursor='hand2', padx=12, pady=6).pack(side='left', padx=(0, 5))
        
        _tk.Button(button_frame, text="Close", command=dialog.destroy, bg='#1a1a1a', fg='#FFFFFF',
                  font=("Segoe UI", 10), relief='flat', cursor='hand2', padx=12, pady=6).pack(side='left')
    
    def _remerge_from_excel_dialog(self, parent_dialog, modpack_name, excel_path):
        """Dialog to confirm and execute re-merge from Excel/CSV file."""
        if not excel_path or not _os.path.isfile(excel_path):
            _messagebox.showerror("Error", "Please load an Excel/CSV file first")
            return
        
        try:
            configs = _EXCEL_MANAGER.load_from_excel(excel_path)
            if modpack_name not in configs:
                _messagebox.showerror("Error", f"Modpack '{modpack_name}' not found in Excel/CSV file")
                return
            
            modpack_config = configs[modpack_name]
            addons = modpack_config.get("addons", [])
            
            if not addons:
                _messagebox.showerror("Error", f"No addons found in modpack '{modpack_name}'")
                return
            
            # Check if all file paths exist
            missing_files = []
            valid_files = []
            for addon in addons:
                path = addon.get("path", "")
                if not path or not _os.path.isfile(path):
                    missing_files.append(addon.get("name", "Unknown"))
                else:
                    valid_files.append(path)
            
            if missing_files:
                _messagebox.showwarning("Missing Files", 
                    f"The following addon files are missing:\n" + "\n".join(missing_files) + 
                    f"\n\nOnly {len(valid_files)} valid files will be merged.")
            
            if not valid_files:
                _messagebox.showerror("Error", "No valid addon files found to merge")
                return
            
            # Confirm dialog
            confirm_dialog = _tk.Toplevel(parent_dialog)
            confirm_dialog.title("Confirm Re-merge")
            confirm_dialog.configure(bg='#1a1a1a')
            confirm_dialog.transient(parent_dialog)
            confirm_dialog.grab_set()
            
            # Main container with padding
            main_frame = _tk.Frame(confirm_dialog, bg='#1a1a1a')
            main_frame.pack(fill='both', expand=True, padx=30, pady=30)
            
            _tk.Label(main_frame, text="🔄 Re-merge Modpack", bg='#1a1a1a', fg='#FFFFFF',
                     font=("Segoe UI", 16, "bold")).pack(pady=(0, 15))
            
            _tk.Label(main_frame, text=f"Modpack: {modpack_name}", bg='#1a1a1a', fg='#CCCCCC',
                     font=("Segoe UI", 11)).pack(pady=(0, 10))
            
            _tk.Label(main_frame, text=f"Addons to merge: {len(valid_files)}", bg='#1a1a1a', fg='#CCCCCC',
                     font=("Segoe UI", 11)).pack(pady=(0, 10))
            
            if missing_files:
                _tk.Label(main_frame, text=f"⚠️ {len(missing_files)} files missing (will be skipped)", bg='#1a1a1a', fg='#f59e0b',
                         font=("Segoe UI", 10)).pack(pady=(0, 20))
            else:
                _tk.Label(main_frame, text="All addon files found ✓", bg='#1a1a1a', fg='#10b981',
                         font=("Segoe UI", 10)).pack(pady=(0, 20))
            
            # Output directory selection
            _tk.Label(main_frame, text="Output Directory:", bg='#1a1a1a', fg='#FFFFFF',
                     font=("Segoe UI", 11)).pack(pady=(0, 5), anchor='w')
            
            output_dir_var = _tk.StringVar(value=self._output_dir_var.get())
            output_entry = _tk.Entry(main_frame, textvariable=output_dir_var, width=50, bg='#0A0A0A', fg='#FFFFFF',
                                   font=("Segoe UI", 10), relief='flat')
            output_entry.pack(pady=(0, 20), fill='x')
            
            def browse_output():
                dir_path = _filedialog.askdirectory(title="Select Output Directory")
                if dir_path:
                    output_dir_var.set(dir_path)
            
            _tk.Button(main_frame, text="Browse", command=browse_output, bg='#9333ea', fg='#FFFFFF',
                     font=("Segoe UI", 10), relief='flat', cursor='hand2').pack(pady=(0, 20))
            
            def confirm_remerge():
                output_dir = output_dir_var.get()
                if not output_dir:
                    _messagebox.showerror("Error", "Please select an output directory")
                    return
                
                try:
                    # Close the Excel manager dialog
                    parent_dialog.destroy()
                    confirm_dialog.destroy()
                    
                    # Load files into the main UI
                    self._files = valid_files
                    self._file_paths = {_os.path.basename(f): f for f in valid_files}
                    self._file_list_data = []
                    for file_path in valid_files:
                        display_name, photo, full_photo = self._get_pack_display_info(file_path)
                        self._file_list_data.append((display_name, file_path, photo, full_photo))
                    
                    # Update the file list UI
                    self._rebuild_autobe_file_list()
                    self._update_file_count()
                    
                    # Set output directory
                    self._output_dir_var.set(output_dir)
                    
                    # Start the merge process
                    self._start_process()
                    
                except Exception as e:
                    _logging.error(f"Error during re-merge: {e}")
                    _messagebox.showerror("Error", f"Failed to start re-merge:\n{e}")
            
            def cancel():
                confirm_dialog.destroy()
            
            button_frame = _tk.Frame(main_frame, bg='#1a1a1a')
            button_frame.pack(pady=(10, 0))
            
            _tk.Button(button_frame, text="🔄 Start Re-merge", command=confirm_remerge, bg='#9333ea', fg='#FFFFFF',
                     font=("Segoe UI", 11, "bold"), relief='flat', cursor='hand2', padx=20, pady=8).pack(side='left', padx=(0, 10))
            
            _tk.Button(button_frame, text="Cancel", command=cancel, bg='#1a1a1a', fg='#FFFFFF',
                     font=("Segoe UI", 11), relief='flat', cursor='hand2', padx=20, pady=8).pack(side='left')
            
            # Center dialog
            confirm_dialog.update_idletasks()
            width = confirm_dialog.winfo_reqwidth()
            height = confirm_dialog.winfo_reqheight()
            x = (confirm_dialog.winfo_screenwidth() // 2) - (width // 2)
            y = (confirm_dialog.winfo_screenheight() // 2) - (height // 2)
            confirm_dialog.geometry(f"{width}x{height}+{x}+{y}")
            confirm_dialog.minsize(width, height)
            
        except Exception as e:
            _logging.error(f"Error loading Excel/CSV for re-merge: {e}")
            _messagebox.showerror("Error", f"Failed to load Excel/CSV file:\n{e}")
    
    def _reset_file_list(self):
        """Reset file list and output selection (called from main thread) after process completes."""
        self._files = []
        self._file_paths = {}
        self._file_list_data = []
        self._output_dir_var.set("")
        self._rebuild_autobe_file_list()
        self._update_file_count()

    def _start_process(self):
        """
        Starts the processing of selected .mcpack files and saves the output to the specified directory.
        """
        # Use full file paths from _files list (listbox now only shows filenames)
        _selected_files = self._files
        # When merge-by-script-version is used, self._out_dir is set to the version subfolder; use it so each group writes to its own folder
        _output_dir = (getattr(self, "_out_dir", None) or "").strip() or self._output_dir_var.get()

        if not _selected_files:
            self._root.after(0, lambda: _messagebox.showerror(_("msg.error"), _("process.select_at_least_one")))
            return
        if not _output_dir:
            self._root.after(0, lambda: _messagebox.showerror(_("msg.error"), _("process.select_output")))
            return

        # Sweep source directories for any _modified.mcpack files left over from a
        # previously interrupted merge and delete them before starting a fresh one.
        _source_dirs = {_os.path.dirname(f) for f in _selected_files if f}
        for _src_dir in _source_dirs:
            try:
                for _leftover in _os.listdir(_src_dir):
                    if _leftover.endswith('_modified.mcpack'):
                        try:
                            _os.remove(_os.path.join(_src_dir, _leftover))
                        except Exception:
                            pass
            except Exception:
                pass

        # Mark merge as active so Discord idle refresh doesn't override merge-specific status
        self._discord_merging = True
        self._merge_discord_start = int(_datetime.datetime.now().timestamp())
        self._discord_merge_last_update = 0
        self._set_discord_merge_step("Starting merge...", f"Loading {len(_selected_files)} addons")

        new_selected_files = []  # Stores all files to be processed (modified and unmodified)
        new_mcpack_paths = []    # Stores paths of modified files for cleanup later
        self._pending_cleanup_mcpacks = new_mcpack_paths  # expose to thread finally for guaranteed cleanup

        for file_path in _selected_files:
            try:
                # Already-processed modified copies — skip the subpack dialog entirely
                if file_path.lower().endswith('_modified.mcpack'):
                    new_selected_files.append(file_path)
                    continue

                # Use the improved _get_manifest_data method which handles comments and malformed JSON
                manifest_data = self._get_manifest_data(file_path)
                if manifest_data is None:
                    _messagebox.showerror(_("msg.error"), _f("process.no_manifest_in_file", path=file_path))
                    continue

                # Check if 'subpacks' exists in manifest
                if 'subpacks' not in manifest_data:
                    # No subpacks found, add the original file to the list
                    new_selected_files.append(file_path)
                    continue

                subpacks = manifest_data['subpacks']
                if not subpacks:
                    # No subpacks defined, add the original file to the list
                    new_selected_files.append(file_path)
                    continue

                # Prepare subpack options for the user
                subpack_options = []
                for subpack in subpacks:
                    folder_name = subpack.get('folder_name', '')
                    name = subpack.get('name', '')
                    if folder_name and name:
                        subpack_options.append(f"{name} (Folder: {folder_name})")

                if not subpack_options:
                    new_selected_files.append(file_path)
                    continue

                # Prompt the user to select a subpack using themed dialog
                file_name_display = _os.path.basename(file_path)
                _sp_short = file_name_display if len(file_name_display) <= 40 else file_name_display[:37] + "..."
                self._set_discord_merge_step("Selecting subpack", _sp_short)
                # Must call from main thread for dialog
                if threading.current_thread() is threading.main_thread():
                    selected_subpack_index = self._show_subpack_selection(file_name_display, subpack_options)
                else:
                    # If in background thread, we need to call on main thread and wait
                    selected_index_var = [None]
                    event = threading.Event()
                    
                    def show_dialog():
                        try:
                            selected_index_var[0] = self._show_subpack_selection(file_name_display, subpack_options)
                        finally:
                            event.set()
                    
                    self._root.after(0, show_dialog)
                    event.wait()  # Wait for dialog to complete
                    selected_subpack_index = selected_index_var[0]

                if selected_subpack_index is None:
                    continue

                selected_subpack = subpacks[selected_subpack_index - 1]
                selected_subpack_name = selected_subpack['folder_name']

                # Create temporary directory
                temp_dir = _tempfile.mkdtemp(prefix='temp_extract_')
                # Extract the selected subpack folder
                with _zipfile.ZipFile(file_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)

                subpack_path = _os.path.join(temp_dir, 'subpacks', selected_subpack_name)

                # Check if subpack_path exists
                if not _os.path.exists(subpack_path):
                    new_selected_files.append(file_path)
                    continue

                # Move the contents of the selected folder outside the 'subpacks' folder
                for item in _os.listdir(subpack_path):
                    s = _os.path.join(subpack_path, item)
                    d = _os.path.join(temp_dir, item)
                    if _os.path.exists(d):
                        if _os.path.isdir(d):
                            _shutil.copytree(s, d, dirs_exist_ok=True)
                        else:
                            _shutil.move(s, d)
                    else:
                        _shutil.move(s, d)

                # Remove the now empty 'subpacks' folder
                subpacks_dir = _os.path.join(temp_dir, 'subpacks')
                if _os.path.exists(subpacks_dir):
                    _shutil.rmtree(subpacks_dir)

                # Repack the .mcpack file — strip 'subpacks' from manifest so
                # the modified copy never triggers the subpack dialog again
                new_mcpack_path = file_path.replace('.mcpack', '_modified.mcpack')
                with _zipfile.ZipFile(new_mcpack_path, 'w') as new_zip_ref:
                    for folder_name, subfolders, filenames in _os.walk(temp_dir):
                        for filename in filenames:
                            file_path_in_temp = _os.path.join(folder_name, filename)
                            arcname = _os.path.relpath(file_path_in_temp, temp_dir)
                            if filename.lower() == 'manifest.json' and arcname.lower() == 'manifest.json':
                                try:
                                    with open(file_path_in_temp, 'r', encoding='utf-8') as _mf:
                                        _mdata = _json.load(_mf)
                                    _mdata.pop('subpacks', None)
                                    new_zip_ref.writestr(arcname, _json.dumps(_mdata, indent=2))
                                    continue
                                except Exception:
                                    pass
                            new_zip_ref.write(file_path_in_temp, arcname)

                # Clean up the temporary directory
                if _os.path.exists(temp_dir):
                    _shutil.rmtree(temp_dir)

                # Add the new modified file to the list
                new_selected_files.append(new_mcpack_path)
                new_mcpack_paths.append(new_mcpack_path)

            except Exception as e:
                log_error(e)
                _messagebox.showerror(_("msg.error"), _f("process.error_processing_file", path=file_path, error=str(e)))
                continue

        if not new_selected_files:
            _messagebox.showerror(_("msg.error"), _("process.no_valid_mcpacks"))
            return

        try:
            _logging.info("Step: _extract_and_store_highest_versions")
            self._extract_and_store_highest_versions()
        except Exception as e:
            _logging.error("_extract_and_store_highest_versions failed", exc_info=True)

        try:
            _logging.info(f"Step: _process_packs ({len(new_selected_files)} files) -> {_output_dir}")
            self._process_packs(new_selected_files, _output_dir)
            _logging.info("Step: _process_packs complete")
        except Exception as e:
            _logging.error("_process_packs failed", exc_info=True)

        try:
            _logging.info("Step: _delete_manifest_files")
            self._delete_manifest_files()
        except Exception as e:
            _logging.error("_delete_manifest_files failed", exc_info=True)

        # Pre-merge: scan scripts for runtime property write conflicts and warn user
        try:
            self._update_progress(1, 2, "Pre-check: Scanning scripts for runtime conflicts...")
            _script_conflicts = self._scan_script_runtime_conflicts(new_selected_files)
            if _script_conflicts:
                _conflict_lines = ["The following packs write to the same entity/world properties at runtime.",
                                   "The LAST pack listed for each conflict will win — others may be partially overridden.",
                                   "You can still merge; this is a warning only.\n"]
                for (_comp, _prop), _pack_hits in sorted(_script_conflicts.items()):
                    if len(_pack_hits) > 1:
                        _conflict_lines.append(f"  {_comp}.{_prop}:")
                        for _pname, _file, _lineno in _pack_hits:
                            _conflict_lines.append(f"    → {_pname}  ({_file}:{_lineno})")
                _conflict_text = "\n".join(_conflict_lines)
                _done = threading.Event()
                def _show_warn():
                    try:
                        _win = _tk.Toplevel(self._root)
                        _win.title("Script Runtime Conflict Report")
                        _win.configure(bg='#1a1a2e')
                        _win.resizable(True, True)
                        _win.geometry("800x600")
                        _win.minsize(600, 400)
                        _win.grab_set()
                        
                        # Main container with padding
                        _container = _tk.Frame(_win, bg='#1a1a2e')
                        _container.pack(fill='both', expand=True, padx=32, pady=32)
                        
                        # Header
                        _tk.Label(_container, text="⚠ Script Runtime Conflict Report",
                                  bg='#1a1a2e', fg='#f97316',
                                  font=("Segoe UI", 14, "bold")).pack(pady=(0, 8))
                        
                        # Subtitle
                        _tk.Label(_container, text="These conflicts cannot be auto-fixed — both scripts run, last write wins.",
                                  bg='#1a1a2e', fg='#cbd5e1',
                                  font=("Segoe UI", 10)).pack(pady=(0, 16))
                        
                        # Text frame with border
                        _txt_frame = _tk.Frame(_container, bg='#16213e', relief='solid', borderwidth=1)
                        _txt_frame.pack(fill='both', expand=True, pady=(0, 20))
                        
                        _inner_frame = _tk.Frame(_txt_frame, bg='#16213e')
                        _inner_frame.pack(fill='both', expand=True, padx=1, pady=1)
                        
                        _sb = _tk.Scrollbar(_inner_frame)
                        _sb.pack(side='right', fill='y')
                        
                        _txt = _tk.Text(_inner_frame, bg='#16213e', fg='#e2e8f0', font=("Consolas", 9),
                                        wrap='word', yscrollcommand=_sb.set, relief='flat', padx=12, pady=12)
                        _txt.pack(fill='both', expand=True, side='left')
                        _sb.config(command=_txt.yview)
                        
                        _txt.insert('1.0', _conflict_text)
                        _txt.config(state='disabled')
                        
                        # Modern button
                        _btn = _tk.Button(_container, text="Continue Merge Anyway",
                                           bg='#7c3aed', fg='#ffffff',
                                           font=("Segoe UI", 10, "bold"), relief='flat',
                                           padx=24, pady=10, cursor='hand2',
                                           activebackground='#6d28d9', activeforeground='#ffffff',
                                           command=lambda: (_win.destroy(), _done.set()))
                        _btn.pack(pady=(0, 0))
                        
                        _win.protocol("WM_DELETE_WINDOW", lambda: (_win.destroy(), _done.set()))
                    except Exception:
                        _done.set()
                self._root.after(0, _show_warn)
                _done.wait()
        except Exception as e:
            _logging.error("Pre-merge script conflict scan failed", exc_info=True)


        try:
            _logging.info("Step 1/4: Creating manifest")
            self._set_discord_merge_step("Step 1/4 — Creating manifest", "Building pack structure")
            self._update_progress(1, 5, "Step 1/4: Creating manifest...")
            self._create_manifest()
            self._update_progress(1, 25, "Step 1/4: Creating manifest... \u2713 Complete")
            _logging.info("Step 1/4 complete")
        except Exception as e:
            _logging.error("Step 1/4 _create_manifest failed", exc_info=True)
            self._update_progress(1, 25, f"Step 1/4: Error - {str(e)}")

        try:
            _logging.info("Step: _move_tick_and_delete_functions")
            self._move_tick_and_delete_functions()
        except Exception as e:
            _logging.error("_move_tick_and_delete_functions failed", exc_info=True)

        try:
            _logging.info(f"Step 2/4: Processing files ({len(new_selected_files)} addons)")
            self._set_discord_merge_step(f"Step 2/4 — Processing {len(new_selected_files)} addons", "Merging files")
            self._update_progress(2, 25, "Step 2/4: Processing files...")
            self._process_files(new_selected_files)
            self._update_progress(2, 50, "Step 2/4: Processing files... \u2713 Complete")
            _logging.info("Step 2/4 complete")
        except Exception as e:
            _logging.error("Step 2/4 _process_files failed", exc_info=True)
            self._update_progress(2, 50, f"Step 2/4: Error - {str(e)}")

        try:
            _logging.info("Step: _move_and_cleanup")
            self._move_and_cleanup()
        except Exception as e:
            _logging.error("_move_and_cleanup failed", exc_info=True)

        try:
            _logging.info("Step 3/4: Updating behavior pack")
            self._set_discord_merge_step("Step 3/4 — Updating behavior pack", "Wiring up scripts & data")
            self._update_progress(3, 50, "Step 3/4: Updating packs...")
            self._update_behavior_pack()
            self._update_progress(3, 75, "Step 3/4: Updating packs... \u2713 Complete")
            _logging.info("Step 3/4 complete")
        except Exception as e:
            _logging.error("Step 3/4 _update_behavior_pack failed", exc_info=True)
            self._update_progress(3, 75, f"Step 3/4: Error - {str(e)}")

        try:
            _logging.info("Step: _merge_flipbook_textures")
            self._merge_flipbook_textures(new_selected_files)
        except Exception as e:
            _logging.error("_merge_flipbook_textures failed", exc_info=True)

        try:
            _logging.info("Step: _merge_textures_list")
            self._merge_textures_list(new_selected_files)
        except Exception as e:
            _logging.error("_merge_textures_list failed", exc_info=True)

        try:
            # Extract and delete zip files
            self._extract_and_delete_zip_files()
        except Exception as e:
            _logging.error("_extract_and_delete_zip_files failed", exc_info=True)
            pass

        # Rename resource_pack.zip → resource_pack.mcpack BEFORE _move_to_resource_pack
        # so that function can actually find the file (it looks for .mcpack, not .zip).
        _rp_zip_early = _os.path.join(self._out_dir, "resource_pack.zip")
        _rp_mcpack_early = _os.path.join(self._out_dir, "resource_pack.mcpack")
        try:
            if _os.path.exists(_rp_zip_early) and not _os.path.exists(_rp_mcpack_early):
                _shutil.move(_rp_zip_early, _rp_mcpack_early)
        except Exception:
            pass

        try:
            # Step 4/4: Move to resource pack (final step)
            self._set_discord_merge_step("Step 4/4 — Finalizing", "Packaging the merged pack")
            self._update_progress(4, 75, "Step 4/4: Finalizing...")
            self._move_to_resource_pack()
            self._update_progress(4, 100, "Step 4/4: Finalizing... \u2713 Complete")
        except Exception as e:
            self._update_progress(4, 100, f"Step 4/4: Error - {str(e)}")
        finally:
            # Clean up any loose flipbook/textures_list files left by the legacy pipeline
            for _loose in ("flipbook_textures.json", "textures_list.json",
                           "flipbook_textures.zip", "textures_list.zip"):
                _loose_path = _os.path.join(self._out_dir, _loose)
                try:
                    if _os.path.isfile(_loose_path):
                        _os.remove(_loose_path)
                except Exception:
                    pass
            # Merge done — release the idle suppression flag so rotating messages resume
            self._discord_merging = False
            self._set_discord_merge_step("Merge complete", f"{len(new_selected_files)} addons packed")

        # Define paths for behavior and resource packs
        _bp_path = _os.path.join(self._out_dir, "behavior_pack.zip")
        _rp_path = _os.path.join(self._out_dir, "resource_pack.zip")
        
        _bp_new_path = _os.path.join(self._out_dir, "behavior_pack.mcpack")
        _rp_new_path = _os.path.join(self._out_dir, "resource_pack.mcpack")
        
        _scripts_path = _os.path.join(self._out_dir, "scripts")
        _temp_dir = _tempfile.mkdtemp(prefix='temp_unpack_')
        _tempr_dir = _tempfile.mkdtemp(prefix='temp_unpack_resource_pack_')
        _flipbook_textures_source = _os.path.join(self._out_dir, "flipbook_textures.json")
        _textures_list_source = _os.path.join(self._out_dir, "textures_list.json")
            

        try:
            # Move and rename the packs if they exist
            if _os.path.exists(_bp_path):
                _shutil.move(_bp_path, _bp_new_path)
        except Exception as e:
            log_error(e)
            _messagebox.showerror(_("msg.error"), _f("process.error_moving_behavior", error=str(e)))

        try:
            # resource_pack.zip may have already been renamed earlier; guard with existence check
            if _os.path.exists(_rp_path) and not _os.path.exists(_rp_new_path):
                _shutil.move(_rp_path, _rp_new_path)
        except Exception as e:
            log_error(e)
            _messagebox.showerror(_("msg.error"), _f("process.error_moving_resource", error=str(e)))

        try:
            if _os.path.exists(_scripts_path):
                _shutil.rmtree(_scripts_path)
        except Exception as e:
            pass

        try:
            if _os.path.exists(_temp_dir):
                _shutil.rmtree(_temp_dir)
        except Exception as e:
            pass

        try:
            if _os.path.exists(_tempr_dir):
                _shutil.rmtree(_tempr_dir)
        except Exception as e:
            pass

        try:
            if _os.path.exists(_flipbook_textures_source):
                _shutil.rmtree(_flipbook_textures_source)
        except Exception as e:
            pass
            

        try:
            if _os.path.exists(_textures_list_source):
                _shutil.rmtree(_textures_list_source)
        except Exception as e:
            pass
            
        # Cleanup: Delete the newly modified .mcpack files
        for new_file in new_mcpack_paths:
            try:
                if _os.path.exists(new_file):
                    _os.remove(new_file)
            except Exception:
                pass

        # Write merge manifest so user can view linked packs and remove one (re-merge without it)
        try:
            _manifest_path = _os.path.join(_output_dir, "_autobe_merge_manifest.json")
            _manifest_data = {
                "source_packs": [_os.path.abspath(p) for p in new_selected_files],
                "output_dir": _os.path.abspath(_output_dir),
            }
            with open(_manifest_path, "w", encoding="utf-8") as _fh:
                _json.dump(_manifest_data, _fh, indent=2)
        except Exception as _e:
            _logging.warning(f"Could not write merge manifest: {_e}")

        # Write merge report with validation checks for debugging common issues
        try:
            self._write_merge_report(
                _output_dir,
                _os.path.join(self._out_dir, "behavior_pack.mcpack"),
                _os.path.join(self._out_dir, "resource_pack.mcpack"),
                new_selected_files,
            )
        except Exception as _e:
            _logging.warning(f"Could not write merge report: {_e}")



    def _send_discord_merge_log(self, pack_files):
        """Send merge log to Discord webhook with addon names, creators, and actual pack icons."""
        webhook_url = "https://discord.com/api/webhooks/1510724383042441397/Bi0UFejBJeohSNCv_nw0JaDPEjXdG1ljDUgDOVFltJ5ZSHL2NbfA4jk_Yaf1A21hJa3K"
        
        if not pack_files:
            return
        
        _logging.info(f"Discord merge log: Processing {len(pack_files)} pack files")
        
        # Deduplicate addons by manifest name (most reliable method)
        seen_manifest_names = set()
        seen_file_paths = set()
        unique_addons = []
        
        for pack_file in pack_files:
            try:
                # Extract addon name from manifest.json
                addon_name = None
                with _zipfile.ZipFile(pack_file, 'r') as zf:
                    if 'manifest.json' in zf.namelist():
                        try:
                            manifest_bytes = zf.read('manifest.json')
                            # Handle manifests with extra data/comments after JSON
                            manifest_str = manifest_bytes.decode('utf-8')
                            # Find the closing brace of the JSON object
                            brace_count = 0
                            json_end = -1
                            for i, char in enumerate(manifest_str):
                                if char == '{':
                                    brace_count += 1
                                elif char == '}':
                                    brace_count -= 1
                                    if brace_count == 0:
                                        json_end = i + 1
                                        break
                            if json_end > 0:
                                manifest_str = manifest_str[:json_end]
                            manifest_data = _json.loads(manifest_str)
                            addon_name = manifest_data.get('header', {}).get('name')
                        except:
                            pass
                
                # If manifest name is available, use it for deduplication
                if addon_name:
                    # Strip BP/RP suffixes and _1, _2, etc. from manifest name for deduplication
                    base_name = _re.sub(
                        r'[_\-\s]*(bp|rp|behaviors?|resources?|behavior[_\-]?pack|resource[_\-]?pack|[_\-\s]*\d+)$',
                        '', addon_name, flags=_re.IGNORECASE).lower()
                    _logging.info(f"Pack: {pack_file}, Manifest name: {addon_name}, Base name: {base_name}")
                    
                    if base_name in seen_manifest_names:
                        _logging.info(f"Filtered as duplicate (manifest): {base_name}")
                        continue
                    seen_manifest_names.add(base_name)
                    unique_addons.append(pack_file)
                    _logging.info(f"Added to unique addons (manifest): {base_name}")
                else:
                    # No manifest name - use filename for deduplication
                    filename = _os.path.basename(pack_file)
                    # Strip _1, _2, RP, BP suffixes from filename
                    base_filename = _re.sub(
                        r'[_\-\s]*(bp|rp|behaviors?|resources?|behavior[_\-]?pack|resource[_\-]?pack|[_\-\s]*\d+)$',
                        '', filename, flags=_re.IGNORECASE).lower()
                    _logging.info(f"Pack: {pack_file}, No manifest name, using filename: {base_filename}")
                    
                    if base_filename in seen_file_paths:
                        _logging.info(f"Filtered as duplicate (filename): {base_filename}")
                        continue
                    seen_file_paths.add(base_filename)
                    unique_addons.append(pack_file)
                    _logging.info(f"Added to unique addons (filename): {base_filename}")
            except Exception as e:
                _logging.warning(f"Failed to deduplicate {pack_file}: {e}")
                unique_addons.append(pack_file)
        
        _logging.info(f"Discord merge log: After deduplication, {len(unique_addons)} unique addons out of {len(pack_files)} total files")
        
        addon_info = []
        for pack_file in unique_addons:
            try:
                with _zipfile.ZipFile(pack_file, 'r') as zf:
                    # Extract addon name and creator from manifest.json
                    addon_name = _os.path.basename(pack_file)
                    creator = "Unknown"
                    pack_icon_data = None
                    
                    if 'manifest.json' in zf.namelist():
                        try:
                            manifest_bytes = zf.read('manifest.json')
                            # Handle manifests with extra data/comments after JSON
                            manifest_str = manifest_bytes.decode('utf-8')
                            # Find the closing brace of the JSON object
                            brace_count = 0
                            json_end = -1
                            for i, char in enumerate(manifest_str):
                                if char == '{':
                                    brace_count += 1
                                elif char == '}':
                                    brace_count -= 1
                                    if brace_count == 0:
                                        json_end = i + 1
                                        break
                            if json_end > 0:
                                manifest_str = manifest_str[:json_end]
                            manifest_data = _json.loads(manifest_str)
                            manifest_name = manifest_data.get('header', {}).get('name', addon_name)
                            # Use filename if manifest name is a placeholder
                            if manifest_name and manifest_name.lower() in ('pack.name', 'pack.description', ''):
                                addon_name = _os.path.basename(pack_file)
                            else:
                                addon_name = manifest_name
                            # Try to extract creator from description or authors field
                            description = manifest_data.get('header', {}).get('description', '')
                            # Check both header.authors and metadata.authors
                            header_authors = manifest_data.get('header', {}).get('authors', [])
                            metadata_authors = manifest_data.get('metadata', {}).get('authors', [])
                            authors = header_authors or metadata_authors
                            
                            _logging.info(f"Pack: {addon_name}, header_authors: {header_authors}, metadata_authors: {metadata_authors}, final_authors: {authors}")
                            
                            if authors:
                                if isinstance(authors, list):
                                    creator = ', '.join(authors)
                                else:
                                    creator = str(authors)
                            elif description:
                                # Check for placeholder descriptions
                                if description.lower() in ('pack.description', 'pack.name', ''):
                                    creator = 'Unknown'
                                else:
                                    # Try to find creator in description
                                    import re as _re
                                    # Look for "by" pattern
                                    match = _re.search(r'by\s+([^\n]+)', description, _re.IGNORECASE)
                                    if match:
                                        creator = match.group(1).strip()
                                    else:
                                        # Try to extract from end of description (last comma-separated value)
                                        parts = [p.strip() for p in description.replace(',', '\n').split('\n')]
                                        if parts:
                                            last_part = parts[-1]
                                            # If last part is short (likely a name), use it
                                            if len(last_part) < 50 and not any(c in last_part for c in '.!?'):
                                                creator = last_part
                                            else:
                                                # Description is too long, probably not a creator name
                                                creator = 'Unknown'
                                        else:
                                            creator = 'Unknown'
                        except Exception as e:
                            _logging.warning(f"Failed to parse manifest for {pack_file}: {e}")
                    
                    # Extract pack_icon.png if present
                    if 'pack_icon.png' in zf.namelist():
                        try:
                            pack_icon_data = zf.read('pack_icon.png')
                        except Exception as e:
                            _logging.warning(f"Failed to extract pack_icon from {pack_file}: {e}")
                    
                    addon_info.append({
                        'name': addon_name,
                        'creator': creator,
                        'description': description,
                        'icon_data': pack_icon_data
                    })
            except Exception as e:
                _logging.warning(f"Failed to extract info from {pack_file}: {e}")
        
        # Create multiple embeds - one per addon, each with its own thumbnail
        # Split into batches to avoid Discord payload size limits (10 embeds per batch)
        batch_size = 10
        total_batches = (len(addon_info) + batch_size - 1) // batch_size
        
        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, len(addon_info))
            batch_addons = addon_info[start_idx:end_idx]
            
            embeds = []
            files = {}
            for i, addon in enumerate(batch_addons, start=start_idx):
                # Clean up description
                desc = addon.get('description', '')
                # Remove placeholder descriptions
                if desc.lower() in ('pack.description', 'pack.name', ''):
                    desc = 'No description'
                else:
                    # Remove creator name from end of description if present
                    creator = addon.get('creator', '')
                    if creator and creator != 'Unknown':
                        # Try to remove creator from end of description
                        if desc.endswith(creator):
                            desc = desc[:-len(creator)].strip()
                            # Remove trailing comma/whitespace
                            desc = desc.rstrip(', ').strip()
                        # Also try removing with comma
                        if desc.endswith(', ' + creator):
                            desc = desc[:-len(', ' + creator)].strip()
                    # If description is now empty after removing creator, use default
                    if not desc or len(desc) < 10:
                        desc = 'No description'
                
                embed = {
                    "title": f"{i + 1}. {addon['name']}",
                    "description": f"Creator: {addon['creator']}\nDescription: {desc}",
                    "color": 3447003,
                    "footer": {"text": f"AutoBE by CodeNex • Batch {batch_num + 1}/{total_batches}"},
                    "timestamp": _datetime.datetime.now().isoformat()
                }
                
                # Use addon's icon as thumbnail if available
                if addon['icon_data']:
                    embed["thumbnail"] = {"url": f"attachment://icon_{i}.png"}
                    files[f"icon_{i}.png"] = addon['icon_data']
                
                embeds.append(embed)
            
            # Send batch to Discord webhook
            try:
                payload = {
                    "embeds": embeds
                }
                
                if files:
                    response = _requests.post(webhook_url, data={"payload_json": _json.dumps(payload)}, files=files, timeout=30)
                else:
                    response = _requests.post(webhook_url, json=payload, timeout=10)
                
                response.raise_for_status()
                _logging.info(f"Discord merge log batch {batch_num + 1}/{total_batches} sent successfully ({len(batch_addons)} addons)")
            except Exception as e:
                _logging.warning(f"Failed to send Discord merge log batch {batch_num + 1}/{total_batches}: {e}")
        
        _logging.info(f"Discord merge log complete: {total_batches} batches, {len(addon_info)} total addons")

        # Send line breaker image at the end to separate users' merge logs
        try:
            separator_image_path = _os.path.join(_os.path.dirname(__file__), "locales", "mf.png")
            if _os.path.isfile(separator_image_path):
                with open(separator_image_path, "rb") as f:
                    separator_data = f.read()

                separator_payload = {
                    "embeds": [{
                        "image": {"url": "attachment://mf.png"},
                        "color": 3447003
                    }]
                }
                files = {"mf.png": separator_data}
                response = _requests.post(webhook_url, data={"payload_json": _json.dumps(separator_payload)}, files=files, timeout=30)
                response.raise_for_status()
                _logging.info("Discord merge log separator image sent successfully")
        except Exception as e:
            _logging.warning(f"Failed to send Discord merge log separator image: {e}")

    def _check_compatibility(self):
        _incompatible_files = []
        _missing_manifest_files = []

        _selected_files = self._files

        for _file in _selected_files:
            with _zipfile.ZipFile(_file, 'r') as _pack_zip:
                _pack_namelist = _pack_zip.namelist()

                if 'manifest.json' not in _pack_namelist:
                    _missing_manifest_files.append(_file)

        if _incompatible_files or _missing_manifest_files:
            _message = "The Following Issues Were Found With Selected MCPacks:\n\n"

            if _missing_manifest_files:
                _message += "Missing manifest.json:\n"
                for _file in _missing_manifest_files:
                    _message += f"- {_os.path.basename(_file)}\n"
                _message += "\n"

            _messagebox.showwarning("Compatibility Check", _message)
        else:
            _messagebox.showinfo(_("compatibility.title"), _("compatibility.all_have_manifest"))

    def _validate_files(self):
        invalid_files = []

        for _file in self._files:
            try:
                with _zipfile.ZipFile(_file, 'r') as _pack_zip:
                    if 'manifest.json' not in _pack_zip.namelist():
                        invalid_files.append(_file)
            except _zipfile.BadZipFile:
                invalid_files.append(_file)

        if invalid_files:
            _message = "The following files are invalid or missing manifest.json:\n\n"
            for _file in invalid_files:
                _message += f"- {_os.path.basename(_file)}\n"
            _messagebox.showerror(_("msg.invalid_files"), _message)
            _logging.error(f"Invalid files detected: {invalid_files}")
            return False
        
        return True

    def _extract_and_store_highest_versions(self):
        if not hasattr(self, 'mcpack_names'):
            _messagebox.showinfo(_("msg.error"), _("msg.no_mcpack_added"))
            return

        # Sections for storing classified packs
        sections = {
            "These Addons Are Using 1.21+ Codes": [],
            "These Addons Are Using 1.20+ Codes": [],
            "These Addons Are Using 1.19+ Codes": [],
            "These Addons Are Using 1.18+ Codes": [],
            "These Addons Are Using 1.17+ Codes": [],
            "These Addons Are Using '1.16 And Below' Codes": []
        }

        # Set initial version as low as possible for comparison
        highest_rp_version = None
        highest_bp_version = None
        
        # Set initial highest versions for dependencies, None to indicate no version found yet
        highest_server_version = None
        highest_server_ui_version = None
        highest_gametest_version = None

        # Store the actual versions (including '-beta') for manifest creation
        highest_server_version_full = None
        highest_server_ui_version_full = None
        highest_gametest_version_full = None

        for _file in self._files:
            manifest_data = self._get_manifest_data(_file)
            if manifest_data and 'header' in manifest_data and 'min_engine_version' in manifest_data['header']:
                min_engine_version_raw = manifest_data['header']['min_engine_version']
                mcpack_name = _os.path.basename(_file)

                # Normalize version to list format [major, minor, patch]
                if isinstance(min_engine_version_raw, str):
                    # Convert string like "1.21.30" to [1, 21, 30]
                    min_engine_version = [int(x) for x in min_engine_version_raw.split('.')]
                elif isinstance(min_engine_version_raw, list):
                    # Already a list, make a copy
                    min_engine_version = list(min_engine_version_raw)
                else:
                    # Try to convert to list
                    min_engine_version = [int(x) for x in str(min_engine_version_raw).split('.')]

                # Ensure version is a 3-part list (pad if necessary)
                while len(min_engine_version) < 3:
                    min_engine_version.append(0)

                # Determine if it's a resource pack or behavior pack
                if 'modules' in manifest_data:
                    for module in manifest_data['modules']:
                        if module['type'] == 'resources':
                            # Compare versions properly: [major, minor, patch]
                            if (highest_rp_version is None or
                                min_engine_version[0] > highest_rp_version[0] or
                                (min_engine_version[0] == highest_rp_version[0] and min_engine_version[1] > highest_rp_version[1]) or
                                (min_engine_version[0] == highest_rp_version[0] and min_engine_version[1] == highest_rp_version[1] and min_engine_version[2] > highest_rp_version[2])):
                                highest_rp_version = min_engine_version
                        elif module['type'] == 'data':
                            # Compare versions properly: [major, minor, patch]
                            if (highest_bp_version is None or
                                min_engine_version[0] > highest_bp_version[0] or
                                (min_engine_version[0] == highest_bp_version[0] and min_engine_version[1] > highest_bp_version[1]) or
                                (min_engine_version[0] == highest_bp_version[0] and min_engine_version[1] == highest_bp_version[1] and min_engine_version[2] > highest_bp_version[2])):
                                highest_bp_version = min_engine_version

                # Extract the dependencies if they exist
                if 'dependencies' in manifest_data:
                    for dependency in manifest_data['dependencies']:
                        module_name = dependency.get('module_name')
                        version = dependency.get('version')

                        if version:
                            # Store the full version (including any '-beta') for later use in manifest
                            version_full = version

                            # Extract only the numeric part for comparison (ignore '-beta' unless specified)
                            if isinstance(version, list):
                                version_numeric_parts = [int(v) for v in version]
                            else:
                                version_numeric_parts = [int(v.split('-')[0]) for v in str(version).split('.')]
                            while len(version_numeric_parts) < 3:
                                version_numeric_parts.append(0)

                            # Compare and update highest versions for dependencies
                            if module_name == "@minecraft/server":
                                if not highest_server_version or version_numeric_parts > highest_server_version:
                                    highest_server_version = version_numeric_parts
                                    highest_server_version_full = version_full  # Keep '-beta' for highest version
                            elif module_name == "@minecraft/server-ui":
                                if not highest_server_ui_version or version_numeric_parts > highest_server_ui_version:
                                    highest_server_ui_version = version_numeric_parts
                                    highest_server_ui_version_full = version_full  # Keep '-beta' for highest version
                            elif module_name == "@minecraft/server-gametest":
                                if not highest_gametest_version or version_numeric_parts > highest_gametest_version:
                                    highest_gametest_version = version_numeric_parts
                                    highest_gametest_version_full = version_full  # Keep '-beta' for highest version

                # Determine section based on min_engine_version
                if min_engine_version[0] == 1:
                    if min_engine_version[1] >= 21:
                        section = "These Addons Are Using 1.21+ Codes"
                    elif min_engine_version[1] == 20:
                        section = "These Addons Are Using 1.20+ Codes"
                    elif min_engine_version[1] == 19:
                        section = "These Addons Are Using 1.19+ Codes"
                    elif min_engine_version[1] == 18:
                        section = "These Addons Are Using 1.18+ Codes"
                    elif min_engine_version[1] == 17:
                        section = "These Addons Are Using 1.17+ Codes"
                    else:
                        section = "These Addons Are Using '1.16 And Below' Codes"
                else:
                    section = "These Addons Are Using '1.16 And Below' Codes"

                sections[section].append(f"{mcpack_name} (Version: {'.'.join(map(str, min_engine_version))})")

        # Set defaults if no versions were found
        if highest_server_version is None:
            highest_server_version = [1, 13, 0]
            highest_server_version_full = "1.13.0"
        if highest_server_ui_version is None:
            highest_server_ui_version = [1, 2, 0]
            highest_server_ui_version_full = "1.2.0"

        # Store the highest versions for later use in manifest creation
        self.highest_rp_version = highest_rp_version
        self.highest_bp_version = highest_bp_version
        self.highest_server_version_full = highest_server_version_full
        self.highest_server_ui_version_full = highest_server_ui_version_full
        self.highest_gametest_version_full = highest_gametest_version_full
        
    def _get_pack_script_api_version(self, manifest_data):
        """Return the script API version string from manifest dependencies (e.g. '1.8.0', '2.5.0', '1.2.0-beta'), or None."""
        if not manifest_data or 'dependencies' not in manifest_data:
            return None
        modules = manifest_data.get('modules') or []
        if isinstance(modules, list) and len(modules) > 0:
            first = modules[0] if isinstance(modules[0], dict) else {}
            if first.get('type') == 'resources':
                return None
        def _ver_tuple(v):
            """Convert '1.19.0-beta' → (1, 19, 0, 0) for numeric comparison."""
            try:
                clean = str(v).strip().lower().replace('-beta', '.1').replace('-', '.')
                parts = clean.split('.')
                return tuple(int(p) if p.isdigit() else 0 for p in parts[:4])
            except Exception:
                return (0, 0, 0, 0)

        version_str = None
        version_tup = (0, 0, 0, 0)
        for dep in manifest_data.get('dependencies') or []:
            if not isinstance(dep, dict):
                continue
            name = dep.get('module_name')
            if name in ('@minecraft/server', '@minecraft/server-ui', '@minecraft/server-gametest'):
                v = dep.get('version')
                if v:
                    vt = _ver_tuple(v)
                    if version_str is None or vt > version_tup:
                        version_str = str(v).strip()
                        version_tup = vt
        return version_str or None

    def _script_api_version_sort_key(self, v):
        """Sort key for version strings: newest first; 'none' last."""
        if v == 'none' or v is None:
            return (0, 0, 0, 0, 1)
        s = v.lower().replace('-beta', '')
        parts = s.split('.')
        try:
            major = int(parts[0]) if len(parts) > 0 else 0
            minor = int(parts[1]) if len(parts) > 1 else 0
            patch = int(parts[2]) if len(parts) > 2 else 0
            is_beta = 'beta' in v.lower()
            return (-major, -minor, -patch, 1 if is_beta else 0, 0)
        except (ValueError, IndexError):
            return (0, 0, 0, 0, 0)

    def _compute_script_api_groups(self):
        """Group pack names by the exact script API version found. Ignores resource packs (RPs don't use scripts). Returns (groups_dict, can_merge)."""
        groups = {}
        for _file in self._files:
            manifest_data = self._get_manifest_data(_file)
            if not manifest_data:
                continue
            modules = manifest_data.get('modules') or []
            if isinstance(modules, list) and len(modules) > 0:
                first = modules[0] if isinstance(modules[0], dict) else {}
                if first.get('type') == 'resources':
                    continue
            name = _os.path.basename(_file)
            ver = self._get_pack_script_api_version(manifest_data)
            key = ver if ver else 'none'
            if key not in groups:
                groups[key] = []
            groups[key].append(name)
        script_keys = [k for k in groups if k != 'none' and groups[k]]
        can_merge = len(script_keys) <= 1
        return groups, can_merge

    def _show_script_api_overlay(self, groups, can_merge):
        """Show in-app overlay: script API groups by found version and can/cannot merge."""
        for widget in self._script_api_overlay.winfo_children():
            widget.destroy()
        self._script_api_overlay.grid_columnconfigure(0, weight=1)
        self._script_api_overlay.grid_rowconfigure(0, weight=1)
        main = _tk.Frame(self._script_api_overlay, bg='#0f1419')
        main.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(0, weight=1)
        card = _tk.Frame(main, bg='#1a1a1a', relief='flat', bd=0)
        card.grid(row=0, column=0, sticky="nsew")
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(1, weight=1)
        _tk.Frame(card, bg='#9333ea', height=3).grid(row=0, column=0, sticky="ew")
        inner = _tk.Frame(card, bg='#1a1a1a')
        inner.grid(row=1, column=0, sticky="nsew", padx=40, pady=30)
        inner.grid_columnconfigure(0, weight=1)
        inner.grid_rowconfigure(3, weight=1)
        _tk.Label(inner, text="📜 " + _("script_api.title"), bg='#1a1a1a', fg='#FFFFFF',
                  font=('Segoe UI', 18, 'bold')).grid(row=0, column=0, pady=(0, 6), sticky="w")
        if can_merge:
            status_text = "✅ Same script API version — these packs can be merged together."
            status_fg = '#10b981'
        else:
            status_text = "❌ Different script API versions — do not merge these together (mixing versions will break scripts)."
            status_fg = '#ef4444'
        _tk.Label(inner, text=status_text, bg='#1a1a1a', fg=status_fg, font=('Segoe UI', 11),
                  wraplength=1200, justify='left').grid(row=1, column=0, pady=(0, 10), sticky="w")

        # Color legend
        legend_frame = _tk.Frame(inner, bg='#111111', highlightthickness=1, highlightbackground='#2d2d2d')
        legend_frame.grid(row=2, column=0, pady=(0, 16), sticky='w')
        _tk.Label(legend_frame, text='  Color key:', bg='#111111', fg='#999999',
                  font=('Segoe UI', 9, 'bold')).pack(side='left', padx=(8, 6), pady=6)
        for dot_col, dot_label in [
            ('#a78bfa', 'Script API v2.x'),
            ('#60a5fa', 'Script API v1.x'),
            ('#f59e0b', 'Beta version'),
            ('#6b7280', 'No script'),
        ]:
            swatch = _tk.Frame(legend_frame, bg=dot_col, width=10, height=10)
            swatch.pack(side='left', padx=(6, 2))
            swatch.pack_propagate(False)
            _tk.Label(legend_frame, text=dot_label, bg='#111111', fg='#d1d5db',
                      font=('Segoe UI', 9)).pack(side='left', padx=(0, 10), pady=6)

        canvas_container = _tk.Frame(inner, bg='#1a1a1a')
        canvas_container.grid(row=3, column=0, sticky="nsew")
        canvas_container.grid_columnconfigure(0, weight=1)
        canvas_container.grid_rowconfigure(0, weight=1)
        canvas = _tk.Canvas(canvas_container, bg='#1a1a1a', highlightthickness=0)
        scrollable = _tk.Frame(canvas, bg='#1a1a1a')

        def _update_scroll(event=None):
            canvas.update_idletasks()
            canvas.configure(scrollregion=canvas.bbox("all"))

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def _scroll_bind_enter(event):
            canvas_container.bind_all("<MouseWheel>", _on_mousewheel)

        def _scroll_bind_leave(event):
            canvas_container.unbind_all("<MouseWheel>")

        def _color_for_version(key):
            if key == 'none':
                return '#6b7280'
            if 'beta' in key.lower():
                return '#f59e0b'
            try:
                major = int(key.split('.')[0])
                return '#a78bfa' if major >= 2 else '#60a5fa'
            except (ValueError, IndexError):
                return '#9333ea'

        scrollable.bind("<Configure>", _update_scroll)
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas.find_all()[0], width=e.width) if canvas.find_all() else None)
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas_container.bind("<Enter>", _scroll_bind_enter)
        canvas_container.bind("<Leave>", _scroll_bind_leave)
        canvas.bind("<Enter>", _scroll_bind_enter)
        scrollable.bind("<Enter>", _scroll_bind_enter)
        row_num = 0
        sorted_keys = sorted(groups.keys(), key=self._script_api_version_sort_key)
        for key in sorted_keys:
            pack_list = sorted(groups[key])
            if not pack_list:
                continue
            if key == 'none':
                title = "No script dependencies"
            else:
                title = f"Script API @minecraft/server {key}"
            color = _color_for_version(key)
            header = _tk.Frame(scrollable, bg=color, height=42)
            header.grid(row=row_num, column=0, sticky="ew", padx=0, pady=(0, 0))
            header.grid_columnconfigure(0, weight=1)
            _tk.Label(header, text=f"  {title}  ·  {len(pack_list)} pack{'s' if len(pack_list) != 1 else ''}  ",
                     bg=color, fg='#FFFFFF', font=('Segoe UI', 12, 'bold'), anchor='w').grid(row=0, column=0, padx=20, pady=10, sticky="w")
            row_num += 1
            for pack_name in pack_list:
                display = (pack_name[:80] + "…") if len(pack_name) > 80 else pack_name
                rf = _tk.Frame(scrollable, bg='#1a1a1a', height=36)
                rf.grid(row=row_num, column=0, sticky="ew", padx=20, pady=2)
                rf.grid_columnconfigure(0, weight=1)
                _tk.Label(rf, text=display, bg='#1a1a1a', fg='#e5e7eb', font=('Segoe UI', 11), anchor='w').grid(row=0, column=0, padx=24, pady=8, sticky="w")
                row_num += 1
            row_num += 6
        scrollable.grid_columnconfigure(0, weight=1)
        canvas.grid(row=0, column=0, sticky="nsew")
        def _close_overlay():
            self._script_api_overlay.grid_remove()
            try:
                self._root.state('normal')
            except Exception:
                pass

        _tk.Button(inner, text=_("common.close"), command=_close_overlay,
                  bg='#9333ea', fg='#FFFFFF', font=('Segoe UI', 11, 'bold'), relief='flat', cursor='hand2',
                  activebackground='#a855f7', padx=30, pady=10).grid(row=4, column=0, pady=(15, 0))
        self._root.after(100, _update_scroll)
        self._script_api_overlay.grid()
        self._script_api_overlay.lift()
        try:
            self._root.state('zoomed')
        except Exception:
            pass

    def _show_conflict_resolution_overlay(self, conflict_list, identifier_manager, done_event):
        """Show overlay listing identifier conflicts; user chooses which pack to keep (or keep all). Blocks until Continue."""
        for w in self._conflict_resolution_overlay.winfo_children():
            w.destroy()
        self._conflict_resolution_overlay.grid_columnconfigure(0, weight=1)
        self._conflict_resolution_overlay.grid_rowconfigure(0, weight=1)
        main = _tk.Frame(self._conflict_resolution_overlay, bg='#0f1419')
        main.grid(row=0, column=0, sticky='nsew', padx=20, pady=20)
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(1, weight=1)
        card = _tk.Frame(main, bg='#1a1a1a', relief='flat')
        card.grid(row=0, column=0, sticky='nsew')
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(1, weight=1)
        _tk.Frame(card, bg='#9333ea', height=3).grid(row=0, column=0, sticky='ew')
        inner = _tk.Frame(card, bg='#1a1a1a')
        inner.grid(row=1, column=0, sticky='nsew', padx=40, pady=30)
        inner.grid_columnconfigure(0, weight=1)
        inner.grid_rowconfigure(2, weight=1)
        title = _("conflict.title") if _("conflict.title") != "conflict.title" else "Identifier conflicts"
        _tk.Label(inner, text="⚔ " + title, bg='#1a1a1a', fg='#FFFFFF', font=('Segoe UI', 18, 'bold')).grid(row=0, column=0, pady=(0, 6), sticky='w')
        desc = _("conflict.desc") if _("conflict.desc") != "conflict.desc" else "Choose which pack to keep for each conflicted identifier, or keep all (prefix)."
        _tk.Label(inner, text=desc, bg='#1a1a1a', fg='#E5E7EB', font=('Segoe UI', 11), wraplength=700, justify='left').grid(row=1, column=0, pady=(0, 16), sticky='w')
        canvas_container = _tk.Frame(inner, bg='#1a1a1a')
        canvas_container.grid(row=2, column=0, sticky='nsew')
        canvas_container.grid_columnconfigure(0, weight=1)
        canvas_container.grid_rowconfigure(0, weight=1)
        canvas = _tk.Canvas(canvas_container, bg='#1a1a1a', highlightthickness=0)
        scrollable = _tk.Frame(canvas, bg='#1a1a1a')
        row_vars = []

        def _update_scroll(_e=None):
            canvas.update_idletasks()
            canvas.configure(scrollregion=canvas.bbox('all'))

        def _on_wheel(e):
            canvas.yview_scroll(int(-1 * (e.delta / 120)), 'units')

        def _scroll_enter(e):
            canvas.bind_all('<MouseWheel>', _on_wheel)

        def _scroll_leave(e):
            try:
                canvas.unbind_all('<MouseWheel>')
            except Exception:
                pass

        scrollable.bind('<Configure>', _update_scroll)
        canvas.create_window((0, 0), window=scrollable, anchor='nw')
        canvas_container.bind('<Enter>', _scroll_enter)
        canvas_container.bind('<Leave>', _scroll_leave)
        canvas.bind('<Enter>', _scroll_enter)
        scrollable.bind('<Enter>', _scroll_enter)
        keep_all_label = "Merge All (combine)"
        for idx, (identifier, pack_paths) in enumerate(conflict_list):
            row = _tk.Frame(scrollable, bg='#252525', height=44)
            row.grid(row=idx, column=0, sticky='ew', padx=0, pady=2)
            row.grid_columnconfigure(0, weight=1)
            id_short = (identifier[:52] + "…") if len(identifier) > 52 else identifier
            _tk.Label(row, text=id_short, bg='#252525', fg='#E5E7EB', font=('Segoe UI', 10), anchor='w').grid(row=0, column=0, padx=12, pady=8, sticky='w')
            choices = [(_os.path.basename(p).replace('.mcpack', '').replace('.mcaddon', '').replace('_modified', ''), p) for p in pack_paths]
            display_choices = [keep_all_label] + [c[0] for c in choices]
            var = _tk.StringVar(self._root, value=keep_all_label)
            row_vars.append((identifier, pack_paths, choices, var))
            om = _tk.OptionMenu(row, var, keep_all_label, *[c[0] for c in choices])
            om.config(bg='#9333ea', fg='#FFFFFF', font=('Segoe UI', 10), anchor='w', relief='flat')
            om.grid(row=0, column=1, padx=12, pady=6)
        scrollable.grid_columnconfigure(0, weight=1)
        canvas.grid(row=0, column=0, sticky='nsew')

        def _on_continue():
            for identifier, pack_paths, choices, var in row_vars:
                val = var.get()
                if val == keep_all_label:
                    identifier_manager.set_user_resolution(identifier, None)
                else:
                    for disp, path in choices:
                        if val == disp:
                            identifier_manager.set_user_resolution(identifier, path)
                            break
            self._conflict_resolution_overlay.grid_remove()
            done_event.set()

        btn_row = _tk.Frame(inner, bg='#1a1a1a')
        btn_row.grid(row=3, column=0, pady=(16, 0))
        btn_text = _("conflict.continue") if _("conflict.continue") != "conflict.continue" else "Continue"
        _tk.Button(btn_row, text=btn_text, command=_on_continue, bg='#9333ea', fg='#FFFFFF', font=('Segoe UI', 11, 'bold'),
                  relief='flat', cursor='hand2', activebackground='#a855f7', padx=30, pady=10).pack(side='left')
        self._root.after(100, _update_scroll)
        self._conflict_resolution_overlay.grid()
        self._conflict_resolution_overlay.lift()

    def _extract_and_show_codes(self):
        """Check Packs: manifest check, obfuscation warning, and script API grouping (can/cannot merge)."""
        self._check_compatibility()
        if not self._files:
            _messagebox.showinfo(_("msg.error"), _("msg.no_mcpack_added"))
            return
        bad_packs = []
        for _file in self._files:
            if self._is_pack_obfuscated(_file):
                bad_packs.append(_os.path.basename(_file))
        if bad_packs:
            msg = "⚠ CRITICAL: CLOSED-SOURCE PACKS DETECTED\n\n"
            msg += "The following packs contain '*/' or Unicode-obfuscated JSON files. "
            msg += "Merging these WILL CORRUPT the final output and cause Minecraft to crash.\n\n"
            msg += "Please REMOVE these files from the list before merging:\n\n• "
            msg += "\n• ".join(bad_packs)
            _messagebox.showwarning("Corrupted Pack Warning", msg)
        else:
            groups, can_merge = self._compute_script_api_groups()
            self._show_script_api_overlay(groups, can_merge)

    def _show_version_check_overlay(self, pack_info_list):
        """Show a themed version check overlay that matches the tool's theme, grouped by version."""
        # Clear existing widgets in overlay
        for widget in self._version_check_overlay.winfo_children():
            widget.destroy()
        
        # Create a variable to track when overlay should close
        overlay_done = _tk.BooleanVar(self._root, False)
        
        # Configure overlay for proper resizing
        self._version_check_overlay.grid_columnconfigure(0, weight=1)
        self._version_check_overlay.grid_rowconfigure(0, weight=1)
        
        # Create main container that fills the overlay
        main_container = _tk.Frame(self._version_check_overlay, bg='#0f1419')
        main_container.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        main_container.grid_columnconfigure(0, weight=1)
        main_container.grid_rowconfigure(1, weight=1)
        
        # Card frame with proper sizing
        card_frame = _tk.Frame(main_container, bg='#1a1a1a', relief='flat', bd=0)
        card_frame.grid(row=0, column=0, sticky="nsew")
        card_frame.grid_columnconfigure(0, weight=1)
        card_frame.grid_rowconfigure(1, weight=1)
        
        # Card border
        border_frame = _tk.Frame(card_frame, bg='#9333ea', height=3)
        border_frame.grid(row=0, column=0, sticky="ew")
        
        # Inner container with proper padding
        inner_frame = _tk.Frame(card_frame, bg='#1a1a1a')
        inner_frame.grid(row=1, column=0, sticky="nsew", padx=25, pady=25)
        inner_frame.grid_columnconfigure(0, weight=1)
        inner_frame.grid_rowconfigure(2, weight=1)
        
        # Title
        title_label = _tk.Label(inner_frame, text="🔍 " + _("version_check.title"), 
                               bg='#1a1a1a', fg='#FFFFFF', 
                               font=('Segoe UI', 16, 'bold'))
        title_label.grid(row=0, column=0, pady=(0, 10), sticky="w")
        
        # Warning message
        warning_label = _tk.Label(inner_frame, 
                                text="⚠️ " + _("version_check.same_version_note"),
                                bg='#1a1a1a', fg='#ff6b6b', 
                                font=('Segoe UI', 10),
                                wraplength=700, justify='left')
        warning_label.grid(row=1, column=0, pady=(0, 15), sticky="w")
        
        if not pack_info_list:
            no_packs_label = _tk.Label(inner_frame, text=_("version_check.no_packs"),
                                      bg='#1a1a1a', fg='#999999', 
                                      font=('Segoe UI', 11))
            no_packs_label.grid(row=2, column=0, pady=20)
        else:
            # Group packs by version
            version_groups = {}
            for pack_info in pack_info_list:
                version = pack_info['version']
                if version not in version_groups:
                    version_groups[version] = []
                version_groups[version].append(pack_info)
            
            # Sort versions (newest first)
            sorted_versions = sorted(version_groups.keys(), reverse=True, 
                                    key=lambda v: tuple(map(int, v.split('.'))))
            
            # Create scrollable frame for categorized pack list
            canvas_container = _tk.Frame(inner_frame, bg='#1a1a1a')
            canvas_container.grid(row=2, column=0, sticky="nsew")
            canvas_container.grid_columnconfigure(0, weight=1)
            canvas_container.grid_rowconfigure(0, weight=1)
            
            canvas = _tk.Canvas(canvas_container, bg='#1a1a1a', highlightthickness=0)
            scrollbar = _tk.Scrollbar(canvas_container, orient='vertical', command=canvas.yview,
                                     bg='#0A0A0A', troughcolor='#1a1a1a',
                                     activebackground='#2d2d2d', width=15)
            scrollable_frame = _tk.Frame(canvas, bg='#1a1a1a')
            
            def update_scroll_region(event=None):
                canvas.update_idletasks()
                canvas.configure(scrollregion=canvas.bbox("all"))
            
            scrollable_frame.bind("<Configure>", update_scroll_region)
            canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas.find_all()[0], width=e.width))
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            # Display packs grouped by version
            row_num = 0
            for version in sorted_versions:
                packs_in_version = version_groups[version]
                count = len(packs_in_version)
                
                # Version category header
                version_header = _tk.Frame(scrollable_frame, bg='#9333ea', height=35)
                version_header.grid(row=row_num, column=0, sticky="ew", padx=0, pady=(0, 8))
                version_header.grid_columnconfigure(0, weight=1)
                
                version_text = f"Version {version} ({count} pack{'s' if count != 1 else ''}) - Safe to merge together"
                _tk.Label(version_header, text=version_text, bg='#9333ea', fg='#FFFFFF',
                         font=('Segoe UI', 12, 'bold'), anchor='w').grid(row=0, column=0, padx=15, pady=8, sticky="w")
                row_num += 1
                
                # Pack rows for this version
                for pack_info in packs_in_version:
                    row_frame = _tk.Frame(scrollable_frame, bg='#1a1a1a')
                    row_frame.grid(row=row_num, column=0, sticky="ew", padx=10, pady=3)
                    row_frame.grid_columnconfigure(0, weight=1)
                    
                    # Pack name (truncate if too long)
                    pack_name = pack_info['name']
                    if len(pack_name) > 50:
                        pack_name = pack_name[:47] + "..."
                    
                    name_label = _tk.Label(row_frame, text=pack_name, bg='#1a1a1a', fg='#FFFFFF',
                                         font=('Segoe UI', 10), anchor='w')
                    name_label.grid(row=0, column=0, padx=(15, 10), pady=6, sticky="ew")
                    
                    type_label = _tk.Label(row_frame, text=pack_info['type'], bg='#1a1a1a', fg='#60a5fa',
                                         font=('Segoe UI', 10))
                    type_label.grid(row=0, column=1, padx=10, pady=6, sticky="e")
                    
                    row_num += 1
            
            # Configure scrollable frame columns
            scrollable_frame.grid_columnconfigure(0, weight=1)
            scrollable_frame.grid_columnconfigure(1, weight=0)
            
            canvas.grid(row=0, column=0, sticky="nsew")
            scrollbar.grid(row=0, column=1, sticky="ns")
            
            # Make canvas expandable
            canvas_container.grid_rowconfigure(0, weight=1)
            canvas_container.grid_columnconfigure(0, weight=1)
        
        def on_close():
            overlay_done.set(True)
            self._version_check_overlay.grid_remove()
        
        # Close button
        button_frame = _tk.Frame(inner_frame, bg='#1a1a1a')
        button_frame.grid(row=3, column=0, pady=(15, 0))
        
        close_btn = _tk.Button(button_frame, text=_("common.close"), command=on_close,
                              bg='#9333ea', fg='#FFFFFF', 
                              font=('Segoe UI', 11, 'bold'),
                              relief='flat', cursor='hand2',
                              activebackground='#a855f7',
                              padx=30, pady=10)
        close_btn.pack()
        
        # Show overlay
        self._version_check_overlay.grid()
        self._version_check_overlay.lift()  # Bring to front
        
        # Update scroll region after a moment to ensure proper sizing
        self._root.after(100, update_scroll_region)
        
        # Wait for user to close
        self._root.wait_variable(overlay_done)

    def _show_version_message(self, sections):
        # Legacy function - kept for backward compatibility but not used
        # Prepare the message to display
        messages = []
        for section, items in sections.items():
            if items:
                messages.append(f"{section}:\n" + "\n".join([f"- {item}" for item in items]))

        if messages:
            warning_message = "Warning: Merging Addons With Different Codes Or format_version May Cause To Break Some Of The Addons' Features, Also Merging The Json UI And The Scripts May Not Be 100% Perfect."
            messages.append(warning_message)
            _messagebox.showinfo(_("addons_used.title"), "\n\n".join(messages))
        else:
            _messagebox.showinfo(_("addons_used.title"), _("version_check.no_packs"))

    def _unify_cross_group_player_json(self, output_root):
        """Merge all groups' entity/player.json into one comprehensive file and
        write it back to EVERY group's resource_pack.mcpack.

        Bedrock picks the entity/player.json from the single highest-priority RP
        that contains it — all others are ignored.  When different version groups
        produce separate merged RPs, one group's player.json wins and the others'
        animation/variable definitions (needed by animation controllers in those
        other groups) are silently dropped.  This step creates one authoritative
        union of all groups' player.json data so every RP carries it, preventing
        cross-group 'can't find animation' and 'unknown variable' errors.
        """
        _VANILLA_PLAYER_ANIMS = {
            "root":                           "controller.animation.player.root",
            "move":                           "animation.player.move",
            "riding.arms":                    "animation.player.riding.arms",
            "riding.legs":                    "animation.player.riding.legs",
            "holding":                        "animation.player.holding",
            "brandish_spear":                 "animation.player.brandish_spear",
            "holding_spyglass":               "animation.player.holding_spyglass",
            "charging":                       "animation.player.charging",
            "attack.positions":               "animation.player.attack.positions",
            "attack.rotations":               "animation.player.attack.rotations",
            "sneaking":                       "animation.player.sneaking",
            "crouch":                         "animation.player.sneaking",
            "bob":                            "animation.player.bob",
            "damage_nearby_mobs":             "animation.player.damage_nearby_mobs",
            "fishing_rod":                    "animation.player.fishing_rod",
            "swimming":                       "animation.player.swimming",
            "swimming.legs":                  "animation.player.swimming.legs",
            "use_item_progress":              "animation.player.use_item_progress",
            "skeleton_attack":                "animation.player.skeleton_attack",
            "sleeping":                       "animation.player.sleeping",
            "cape":                           "animation.player.cape",
            "first_person_base_pose":         "animation.player.first_person_base_pose",
            "first_person_empty_hand":        "animation.player.first_person_empty_hand",
            "first_person_swap_item":         "animation.player.first_person_swap_item",
            "first_person_attack_controller": "controller.animation.player.first_person_attack",
            "first_person_map_controller":    "controller.animation.player.first_person_map",
            "first_person_crossbow_equipped": "animation.player.first_person_crossbow_equipped",
            "first_person_breathing_bob":     "animation.player.first_person_breathing_bob",
            "third_person_bow":               "animation.player.third_person_bow",
            "third_person_crossbow":          "animation.player.third_person_crossbow",
            "third_person_die":               "animation.player.third_person_die",
            "third_person_map_controller":    "controller.animation.player.third_person_map",
            "blink":                          "controller.animation.player.blink",
            "totem_animation":                "animation.player.totem",
            "totem_controller":               "controller.animation.player.totem",
            "look_at_target_ui":              "animation.player.look_at_target.ui",
            "look_at_target_default":         "animation.player.look_at_target.default",
            "look_at_target_gliding":         "animation.player.look_at_target.gliding",
            "look_at_target_swimming":        "animation.player.look_at_target.swimming",
            "look_at_target_inverted":        "animation.player.look_at_target.inverted",
        }
        _ENTITY_CTX_QUERIES = (
            'query.is_item_name_any',
            'query.is_item_any_tag',
            'query.equipped_item_any_tag',
            'query.property(',
            'query.has_equippable(',
            'query.get_equipped_item_name(',
        )
        try:
            rp_paths = []
            unified = {}
            for entry in _os.scandir(output_root):
                if not entry.is_dir():
                    continue
                rp = _os.path.join(entry.path, 'resource_pack.mcpack')
                if not _os.path.isfile(rp):
                    continue
                rp_paths.append(rp)
                try:
                    with _zipfile.ZipFile(rp, 'r') as zf:
                        if 'entity/player.json' in zf.namelist():
                            data = _json.loads(zf.read('entity/player.json'))
                            self._merge_json_data(unified, data)
                except Exception:
                    pass

            if not unified or not rp_paths:
                return

            desc = unified.get('minecraft:client_entity', {}).get('description', {})
            if not isinstance(desc, dict):
                return

            scripts = desc.setdefault('scripts', {})

            # Move entity-context queries out of initialize into pre_animation
            try:
                init_raw   = scripts.get('initialize', [])
                init_list  = list(init_raw) if isinstance(init_raw, list) else []
                pre_list   = scripts.setdefault('pre_animation', [])
                if not isinstance(pre_list, list):
                    pre_list = []
                    scripts['pre_animation'] = pre_list
                keep_init, move_pre = [], []
                for expr in init_list:
                    if isinstance(expr, str) and any(q in expr for q in _ENTITY_CTX_QUERIES):
                        move_pre.append(expr)
                    else:
                        keep_init.append(expr)
                if move_pre:
                    scripts['initialize'] = keep_init
                    existing_pre = ' '.join(str(x) for x in pre_list)
                    for mv in move_pre:
                        if mv not in existing_pre:
                            pre_list.append(mv)
            except Exception:
                pass

            # De-duplicate: remove from pre_animation any simple variable
            # initializations (variable.X = N;) that already appear in initialize.
            # Having them in both resets the variable every frame, breaking
            # addons that dynamically change that variable (e.g. melee_spear_equipped).
            try:
                _init_for_dedup = scripts.get('initialize', [])
                _pre_for_dedup  = scripts.get('pre_animation', [])
                if isinstance(_init_for_dedup, list) and isinstance(_pre_for_dedup, list):
                    _init_text = ' '.join(str(x) for x in _init_for_dedup)
                    _clean_pre = []
                    for _pe_expr in _pre_for_dedup:
                        if not isinstance(_pe_expr, str):
                            _clean_pre.append(_pe_expr)
                            continue
                        # Simple zero-init pattern: variable.X = <literal>;
                        _is_simple_init = (
                            _pe_expr.strip().startswith('variable.') and
                            '=' in _pe_expr and
                            not any(q in _pe_expr for q in _ENTITY_CTX_QUERIES) and
                            not any(fn in _pe_expr for fn in ('query.', 'math.', 'Math.')) and
                            _pe_expr.strip() in _init_text
                        )
                        if not _is_simple_init:
                            _clean_pre.append(_pe_expr)
                    scripts['pre_animation'] = _clean_pre
            except Exception:
                pass

            # Backfill vanilla animation aliases
            try:
                anims = desc.setdefault('animations', {})
                if not isinstance(anims, dict):
                    anims = {}
                    desc['animations'] = anims
                for alias, anim_id in _VANILLA_PLAYER_ANIMS.items():
                    anims.setdefault(alias, anim_id)
            except Exception:
                pass

            # Stub any animate-block short-names that are still missing
            try:
                animate_blk = scripts.get('animate', [])
                if isinstance(animate_blk, list):
                    defined = set(anims.keys())
                    for ent in animate_blk:
                        a = ent if isinstance(ent, str) else (next(iter(ent), None) if isinstance(ent, dict) else None)
                        if a and a not in defined:
                            anims[a] = 'animation.player.move'
                            defined.add(a)
            except Exception:
                pass

            # De-duplicate scripts.animate by name: dict-with-condition beats plain string.
            # _union_merge_list uses full JSON fingerprint, so "root" (str) and
            # {"root": "!query.is_riding"} (dict) are treated as different items and
            # both survive → the root controller runs twice → legs/arms go crazy.
            try:
                _anim_blk = scripts.get('animate', [])
                if isinstance(_anim_blk, list):
                    _anim_seen = {}
                    for _ae in _anim_blk:
                        if isinstance(_ae, str):
                            if _ae not in _anim_seen:
                                _anim_seen[_ae] = _ae
                        elif isinstance(_ae, dict) and _ae:
                            _ak = next(iter(_ae))
                            _anim_seen[_ak] = _ae  # dict wins over any earlier plain string
                    scripts['animate'] = list(_anim_seen.values())
            except Exception:
                pass

            # De-duplicate render_controllers by controller name (first occurrence wins).
            # Multiple packs list the same render controller with slightly different condition
            # strings (spacing) → all survive → player renders multiple times simultaneously.
            try:
                _rc_list = desc.get('render_controllers', [])
                if isinstance(_rc_list, list):
                    _rc_seen = {}
                    for _rce in _rc_list:
                        if isinstance(_rce, dict) and _rce:
                            _rcn = next(iter(_rce))
                            if _rcn not in _rc_seen:
                                _rc_seen[_rcn] = _rce
                        elif isinstance(_rce, str) and _rce not in _rc_seen:
                            _rc_seen[_rce] = _rce
                    desc['render_controllers'] = list(_rc_seen.values())
            except Exception:
                pass

            unified_str = _json.dumps(unified, indent=2)

            # Write the unified player.json back into every group's resource_pack.mcpack
            for rp in rp_paths:
                _tmpfd, _tmppath = None, None
                try:
                    _tmpfd, _tmppath = _tempfile.mkstemp(
                        dir=_os.path.dirname(rp), suffix='.autobe_tmp')
                    _os.close(_tmpfd)
                    _tmpfd = None
                    with _zipfile.ZipFile(rp, 'r') as zin:
                        with _zipfile.ZipFile(_tmppath, 'w', _zipfile.ZIP_DEFLATED) as zout:
                            wrote_player = False
                            for item in zin.infolist():
                                if item.filename in ('entity/player.json', 'entity/player.entity.json'):
                                    if not wrote_player:
                                        zout.writestr('entity/player.entity.json', unified_str)
                                        wrote_player = True
                                    # drop duplicate entry
                                else:
                                    zout.writestr(item, zin.read(item.filename))
                            if not wrote_player:
                                zout.writestr('entity/player.entity.json', unified_str)
                    _os.replace(_tmppath, rp)
                    _tmppath = None
                except Exception:
                    pass
                finally:
                    if _tmpfd is not None:
                        try:
                            _os.close(_tmpfd)
                        except Exception:
                            pass
                    if _tmppath and _os.path.exists(_tmppath):
                        try:
                            _os.unlink(_tmppath)
                        except Exception:
                            pass
        except Exception:
            pass

    def _unify_cross_group_player_anims(self, output_root):
        """Merge player animation / animation-controller / render-controller files
        from ALL groups' RPs into unified files and write them back to every group.

        When different version groups produce separate merged RPs (e.g. 'none' for
        Play-as-Link, '1_x' for Paraglider), Bedrock can only honour ONE group's
        animations/player.animation.json — the one in the highest-priority RP.  The
        other groups' custom animations are silently lost.  This step creates one
        authoritative union of all groups' player animation data so every RP carries
        the complete set, regardless of load order.

        Merge strategy: first-wins per individual animation / controller ID.
        Each animation is a self-contained definition; partially merging two packs'
        versions of the same animation produces broken keyframes, so we keep the
        first-encountered complete definition and add any IDs not yet seen.
        """
        _PLAYER_ANIM_FILES = [
            'animations/player.animation.json',
            'animations/player_firstperson.animation.json',
            'animation_controllers/player.animation_controllers.json',
            'render_controllers/player.render_controllers.json',
            'entity/player.entity.json',
        ]
        # Top-level dict keys that hold individual named entries (first-wins per entry)
        _ENTRY_DICT_KEYS = {'animations', 'animation_controllers', 'render_controllers', 'minecraft:client_entity'}

        def _merge_anim_first_wins(target, source):
            """Merge source into target with first-wins per named animation/controller entry."""
            for k, v in source.items():
                if k not in target:
                    target[k] = v
                elif k in _ENTRY_DICT_KEYS and isinstance(target[k], dict) and isinstance(v, dict):
                    for entry_id, entry_data in v.items():
                        target[k].setdefault(entry_id, entry_data)
                # Special handling for description section in entity files
                elif k == 'description' and isinstance(target[k], dict) and isinstance(v, dict):
                    # Prioritize source description entirely to preserve custom features
                    target[k] = v
                # primitives like format_version: keep first (do nothing)

        def _merge_mobs_json(target, source):
            """Merge models/mobs.json: union geometry IDs + bone-union per geometry.
            mobs.json top-level keys are geometry IDs (e.g. 'geometry.humanoid.custom:...')
            that each contain a 'bones' list.  Different packs ship slightly different
            versions — e.g. BetterCombat is missing the 'hat' bone that the Link Pack
            adds to geometry.humanoid.custom.  This union ensures every bone that any
            pack defines is present in the final merged geometry.
            """
            for k, v in source.items():
                if k == 'format_version':
                    target.setdefault(k, v)
                elif k not in target:
                    # New geometry ID: add it entirely
                    target[k] = v
                elif isinstance(target[k], dict) and isinstance(v, dict):
                    # Same geometry ID in two packs: union bones by name
                    if isinstance(target[k].get('bones'), list) and isinstance(v.get('bones'), list):
                        _existing_names = {b.get('name') for b in target[k]['bones'] if isinstance(b, dict)}
                        for _bone in v['bones']:
                            if isinstance(_bone, dict) and _bone.get('name') not in _existing_names:
                                target[k]['bones'].append(_bone)
                                _existing_names.add(_bone.get('name'))

        try:
            rp_paths = []
            unified = {p: None for p in _PLAYER_ANIM_FILES}
            unified_mobs = None   # models/mobs.json: bone-union merge
            player_textures = {}  # path → bytes, player texture files that only exist in one group

            for entry in sorted(_os.scandir(output_root), key=lambda e: e.name, reverse=True):
                if not entry.is_dir():
                    continue
                rp = _os.path.join(entry.path, 'resource_pack.mcpack')
                if not _os.path.isfile(rp):
                    continue
                rp_paths.append(rp)
                _logging.info(f"[_unify_cross_group_player_anims] Processing RP: {rp}")
                try:
                    with _zipfile.ZipFile(rp, 'r') as zf:
                        names = zf.namelist()
                        for anim_file in _PLAYER_ANIM_FILES:
                            if anim_file in names:
                                try:
                                    data = _json.loads(zf.read(anim_file))
                                    if unified[anim_file] is None:
                                        import copy as _copy
                                        unified[anim_file] = _copy.deepcopy(data)
                                        _logging.info(f"[_unify_cross_group_player_anims] Initialized {anim_file} from {rp}")
                                    else:
                                        _merge_anim_first_wins(unified[anim_file], data)
                                        _logging.info(f"[_unify_cross_group_player_anims] Merged {anim_file} from {rp}")
                                except Exception as _e:
                                    _logging.error(f"[_unify_cross_group_player_anims] Failed to process {anim_file} in {rp}: {_e}", exc_info=True)
                        # Bone-union merge for models/mobs.json
                        if 'models/mobs.json' in names:
                            try:
                                import copy as _copy
                                mobs_data = _json.loads(zf.read('models/mobs.json'))
                                if unified_mobs is None:
                                    unified_mobs = _copy.deepcopy(mobs_data)
                                    _logging.info(f"[_unify_cross_group_player_anims] Initialized models/mobs.json from {rp}")
                                else:
                                    _merge_mobs_json(unified_mobs, mobs_data)
                                    _logging.info(f"[_unify_cross_group_player_anims] Merged models/mobs.json from {rp}")
                            except Exception as _e:
                                _logging.error(f"[_unify_cross_group_player_anims] Failed to process models/mobs.json in {rp}: {_e}", exc_info=True)
                        # Collect player-specific textures that only exist in this RP
                        # (e.g. Link Pack's textures/entity/steve.png)
                        for _tex_name in names:
                            if not _tex_name.startswith('textures/entity/') or not _tex_name.endswith('.png'):
                                continue
                            # Only collect if not already seen in another group
                            if _tex_name not in player_textures:
                                try:
                                    player_textures[_tex_name] = zf.read(_tex_name)
                                except Exception as _e:
                                    _logging.error(f"[_unify_cross_group_player_anims] Failed to read texture {_tex_name} in {rp}: {_e}", exc_info=True)
                except Exception as _e:
                    _logging.error(f"[_unify_cross_group_player_anims] Failed to process RP {rp}: {_e}", exc_info=True)

            if not rp_paths:
                _logging.warning("[_unify_cross_group_player_anims] No resource packs found to process")
                return

            serialised = {}
            for anim_file, data in unified.items():
                if data:
                    serialised[anim_file] = _json.dumps(data, indent=2)
            if unified_mobs:
                serialised['models/mobs.json'] = _json.dumps(unified_mobs, indent=2)

            if not serialised and not player_textures:
                _logging.warning("[_unify_cross_group_player_anims] No data to write back")
                return

            _logging.info(f"[_unify_cross_group_player_anims] Writing unified files to {len(rp_paths)} RPs: {list(serialised.keys())}")

            for rp in rp_paths:
                _tmpfd, _tmppath = None, None
                try:
                    _tmpfd, _tmppath = _tempfile.mkstemp(
                        dir=_os.path.dirname(rp), suffix='.autobe_tmp')
                    _os.close(_tmpfd)
                    _tmpfd = None
                    with _zipfile.ZipFile(rp, 'r') as zin:
                        with _zipfile.ZipFile(_tmppath, 'w', _zipfile.ZIP_DEFLATED) as zout:
                            written = set()
                            for item in zin.infolist():
                                if item.filename in serialised:
                                    zout.writestr(item, serialised[item.filename])
                                    written.add(item.filename)
                                else:
                                    zout.writestr(item, zin.read(item.filename))
                            for anim_file, content in serialised.items():
                                if anim_file not in written:
                                    zout.writestr(anim_file, content)
                                    written.add(anim_file)
                            # Distribute player-specific textures to all groups
                            for _tex_path, _tex_data in player_textures.items():
                                if _tex_path not in written and _tex_path not in [n.filename for n in zin.infolist()]:
                                    zout.writestr(_tex_path, _tex_data)
                    _os.replace(_tmppath, rp)
                    _tmppath = None
                    _logging.info(f"[_unify_cross_group_player_anims] Successfully updated {rp}")
                except Exception as _e:
                    _logging.error(f"[_unify_cross_group_player_anims] Failed to update RP {rp}: {_e}", exc_info=True)
                finally:
                    if _tmpfd is not None:
                        try:
                            _os.close(_tmpfd)
                        except Exception:
                            pass
                    if _tmppath and _os.path.exists(_tmppath):
                        try:
                            _os.unlink(_tmppath)
                        except Exception:
                            pass
        except Exception as _e:
            _logging.error(f"[_unify_cross_group_player_anims] Top-level exception: {_e}", exc_info=True)

    def _unify_cross_group_atlas_files(self, output_root):
        """Merge terrain_texture.json, item_texture.json, and blocks.json from ALL
        groups' merged RPs into one unified set and write it back to every group.

        Custom blocks whose BP lives in one version group (e.g. 2_x) keep their
        terrain_texture / item_texture registrations inside that group's RP only.
        When Bedrock applies multiple merged RPs, it may not reliably merge
        terrain_texture.json from a lower-priority pack (behaviour varies across
        engine versions and RP-stack orderings).  A block defined in the 2_x BP
        referencing texture ID 'warped_planks' would therefore not find its
        registration in the 1_x RP (which has no entry for it) and fall back to
        the missing-texture dirt appearance.

        Fix: union all groups' texture_data (first-wins per entry so no pack can
        silently overwrite another's custom texture IDs) and write the combined
        atlas to every group's resource_pack.mcpack.
        """
        _ATLAS_FILES = [
            'textures/terrain_texture.json',
            'textures/item_texture.json',
            'blocks.json',
        ]
        try:
            rp_paths = []
            unified = {f: None for f in _ATLAS_FILES}

            for entry in sorted(_os.scandir(output_root), key=lambda e: e.name):
                if not entry.is_dir():
                    continue
                rp = _os.path.join(entry.path, 'resource_pack.mcpack')
                if not _os.path.isfile(rp):
                    continue
                rp_paths.append(rp)
                try:
                    with _zipfile.ZipFile(rp, 'r') as zf:
                        names = zf.namelist()
                        for atlas_file in _ATLAS_FILES:
                            if atlas_file not in names:
                                continue
                            try:
                                import copy as _copy
                                data = _json.loads(zf.read(atlas_file))
                                if unified[atlas_file] is None:
                                    unified[atlas_file] = _copy.deepcopy(data)
                                else:
                                    # Union merge: recurse into 'texture_data' or top-level
                                    # dict, keeping first-wins for conflicting IDs so each
                                    # pack's own texture registrations are always preserved.
                                    _base = unified[atlas_file]
                                    for k, v in data.items():
                                        if k not in _base:
                                            _base[k] = v
                                        elif isinstance(_base[k], dict) and isinstance(v, dict):
                                            # texture_data / item entries: first-wins per key
                                            for ek, ev in v.items():
                                                _base[k].setdefault(ek, ev)
                                        # primitives (format_version, etc.): keep first
                            except Exception:
                                pass
                except Exception:
                    pass

            if not rp_paths:
                return

            serialised = {}
            for atlas_file, data in unified.items():
                if data:
                    serialised[atlas_file] = _json.dumps(data, indent=2)

            if not serialised:
                return

            # --- Geometry distribution ---
            # Collect models/entity/*.geo.json and models/blocks/*.geo.json from all
            # groups.  For each unique path union-merge the minecraft:geometry arrays
            # (first-wins per geometry ID) so every group ends up with the full set.
            # This ensures geometry.table / geometry.chair (only in 2_x RP) are found
            # when 1_x RP is the highest-priority active pack.
            _geo_prefixes = ('models/entity/', 'models/blocks/')
            _geo_unified = {}   # path -> merged geometry JSON data
            for _rp2 in rp_paths:
                try:
                    with _zipfile.ZipFile(_rp2, 'r') as _zf2:
                        for _n in _zf2.namelist():
                            if not any(_n.startswith(_p) for _p in _geo_prefixes):
                                continue
                            if not _n.endswith('.geo.json'):
                                continue
                            try:
                                import copy as _copy
                                _gdata = _json.loads(_zf2.read(_n))
                                if _n not in _geo_unified:
                                    _geo_unified[_n] = _copy.deepcopy(_gdata)
                                else:
                                    # Union-merge minecraft:geometry arrays
                                    _base_g = _geo_unified[_n]
                                    _src_g = _gdata
                                    if (isinstance(_base_g.get('minecraft:geometry'), list)
                                            and isinstance(_src_g.get('minecraft:geometry'), list)):
                                        _existing_ids = {
                                            g.get('description', {}).get('identifier')
                                            for g in _base_g['minecraft:geometry']
                                            if isinstance(g, dict)
                                        }
                                        for _geo_entry in _src_g['minecraft:geometry']:
                                            _eid = (_geo_entry.get('description', {}).get('identifier')
                                                    if isinstance(_geo_entry, dict) else None)
                                            if _eid not in _existing_ids:
                                                _base_g['minecraft:geometry'].append(_geo_entry)
                                                _existing_ids.add(_eid)
                            except Exception:
                                pass
                except Exception:
                    pass

            # Serialise merged geometry files
            _geo_serialised = {}
            for _geo_path, _geo_data in _geo_unified.items():
                try:
                    _geo_serialised[_geo_path] = _json.dumps(_geo_data, indent=2)
                except Exception:
                    pass

            for rp in rp_paths:
                _tmpfd, _tmppath = None, None
                try:
                    _tmpfd, _tmppath = _tempfile.mkstemp(
                        dir=_os.path.dirname(rp), suffix='.autobe_tmp')
                    _os.close(_tmpfd)
                    _tmpfd = None
                    with _zipfile.ZipFile(rp, 'r') as zin:
                        with _zipfile.ZipFile(_tmppath, 'w', _zipfile.ZIP_DEFLATED) as zout:
                            written = set()
                            for item in zin.infolist():
                                if item.filename in serialised:
                                    zout.writestr(item, serialised[item.filename])
                                    written.add(item.filename)
                                elif item.filename in _geo_serialised:
                                    zout.writestr(item, _geo_serialised[item.filename])
                                    written.add(item.filename)
                                else:
                                    zout.writestr(item, zin.read(item.filename))
                            for atlas_file, content in serialised.items():
                                if atlas_file not in written:
                                    zout.writestr(atlas_file, content)
                            for _geo_path, _geo_content in _geo_serialised.items():
                                if _geo_path not in written:
                                    zout.writestr(_geo_path, _geo_content)
                    _os.replace(_tmppath, rp)
                    _tmppath = None
                except Exception:
                    pass
                finally:
                    if _tmpfd is not None:
                        try:
                            _os.close(_tmpfd)
                        except Exception:
                            pass
                    if _tmppath and _os.path.exists(_tmppath):
                        try:
                            _os.unlink(_tmppath)
                        except Exception:
                            pass
        except Exception:
            pass

    def _unify_cross_group_hud_files(self, output_root):
        """Merge ui/hud_screen.json and ui/_ui_defs.json from ALL groups' RPs into
        one unified file and write it back to every group's resource_pack.mcpack.

        When different version groups produce separate merged RPs, Bedrock only
        honours one pack's hud_screen.json modifications per key — the others are
        silently lost.  For example, Paraglider's 150 KB hud_screen (1_x RP) would
        override the temperature/mqps HUD patches (2_x RP), causing temperature
        state text to show as raw title text and mqps bars to render incorrectly.
        This step creates one authoritative union of all groups' UI modifications so
        every RP carries the complete hud_screen and _ui_defs registration list.
        """
        try:
            _UI_FILES = ['ui/hud_screen.json', 'ui/_global_variables.json']
            _UI_DEFS  = 'ui/_ui_defs.json'

            rp_paths = []
            # merged_hud[file_path] = combined dict
            merged = {p: {} for p in _UI_FILES}
            merged_ui_defs = []          # deduplicated list of ui_def entries
            merged_ui_defs_set = set()
            # .uids patches: path → (old, new) string replacements
            # NOTE: hud_temp.uids correctly uses source_control_name:"temp_data_binding"
            # which matches the element injected into root_panel as
            # "temp_data_binding@hud_wt_temp.temp_data" by the Water Temperature
            # System's hud_screen.json.  No patch is needed here.
            _UIDS_PATCHES = {}
            # Collect .uids files that need patching across all RPs
            uids_to_patch = {}   # path → raw content after patching

            for entry in sorted(_os.scandir(output_root), key=lambda e: e.name):
                if not entry.is_dir():
                    continue
                rp = _os.path.join(entry.path, 'resource_pack.mcpack')
                if not _os.path.isfile(rp):
                    continue
                rp_paths.append(rp)
                try:
                    with _zipfile.ZipFile(rp, 'r') as zf:
                        names = zf.namelist()
                        # Merge plain UI JSON files (dict union, later groups win)
                        for ui_path in _UI_FILES:
                            if ui_path in names:
                                try:
                                    raw = zf.read(ui_path).decode('utf-8', 'replace')
                                    data = _json.loads(_re.sub(r'//[^\n]*', '', raw))
                                    # Special handling for factories: first-wins to preserve MQPS functionality
                                    if ui_path == 'ui/hud_screen.json':
                                        # Preserve factories with first-wins strategy
                                        for key, value in data.items():
                                            if 'factory' in key.lower():
                                                if key not in merged[ui_path]:
                                                    merged[ui_path][key] = value
                                            elif key == 'hud_actionbar_text' and '$atext' in value:
                                                # Preserve $atext binding from MQPS
                                                if key not in merged[ui_path] or '$atext' not in merged[ui_path][key]:
                                                    merged[ui_path][key] = value
                                            else:
                                                # Normal merge for other elements
                                                self._deep_merge_dicts(merged[ui_path], {key: value},
                                                                       _combine_visible=True)
                                    else:
                                        # Normal merge for other UI files
                                        self._deep_merge_dicts(merged[ui_path], data,
                                                               _combine_visible=True)
                                except Exception:
                                    pass
                        # Merge _ui_defs.json arrays (union, preserve order)
                        if _UI_DEFS in names:
                            try:
                                raw = zf.read(_UI_DEFS).decode('utf-8', 'replace')
                                defs_data = _json.loads(_re.sub(r'//[^\n]*', '', raw))
                                for entry_def in defs_data.get('ui_defs', []):
                                    if entry_def not in merged_ui_defs_set:
                                        merged_ui_defs.append(entry_def)
                                        merged_ui_defs_set.add(entry_def)
                            except Exception:
                                pass
                        # Collect and patch known-broken .uids files
                        for uids_path, patches in _UIDS_PATCHES.items():
                            if uids_path in names:
                                try:
                                    raw = zf.read(uids_path).decode('utf-8', 'replace')
                                    for old, new in patches:
                                        raw = raw.replace(old, new)
                                    uids_to_patch[uids_path] = raw.encode('utf-8')
                                except Exception:
                                    pass
                        # Collect ALL .uids files for cross-group distribution.
                        # Each group's _ui_defs.json now lists entries from all
                        # groups, so every group's RP must physically contain the
                        # referenced .uids files — even if the originating pack
                        # was only in one group.  Last-writer-wins across groups
                        # is fine since the files are identical across groups.
                        for _uids_name in names:
                            if _uids_name.endswith('.uids') and _uids_name not in uids_to_patch:
                                try:
                                    uids_to_patch[_uids_name] = zf.read(_uids_name)
                                except Exception:
                                    pass
                except Exception:
                    pass

            if not rp_paths:
                return

            # NOTE: Do NOT replace $atext with #actionbar_text here.
            # MQPS uses hud_actionbar_text_factory which provides $actionbar_text as a
            # factory-scoped variable to all factory-instantiated elements (hud_actionbar
            # _text, more_hunger_bar, more_health_bar).  $atext='$actionbar_text' resolves
            # correctly inside this factory context.  Using #actionbar_text in a Molang
            # 'visible' expression does NOT work — # bindings are text-property-only and
            # evaluate to 0 in Molang arithmetic → '%.4s'*0='' ≠ 'mqps' → NOT false=TRUE
            # → hud_actionbar_text ALWAYS visible → raw 'mqps...' text always bleeds.

            # Serialise merged results
            serialised = {}        # path → str  (for JSON files)
            serialised_bin = {}    # path → bytes (for binary/uids files)
            for ui_path, data in merged.items():
                if data:
                    serialised[ui_path] = _json.dumps(data, indent=2, ensure_ascii=False)
            if merged_ui_defs:
                serialised[_UI_DEFS] = _json.dumps({'ui_defs': merged_ui_defs}, indent=2, ensure_ascii=False)
            for uids_path, content_bytes in uids_to_patch.items():
                serialised_bin[uids_path] = content_bytes

            if not serialised and not serialised_bin:
                return

            # Write unified files back into every group's resource_pack.mcpack
            for rp in rp_paths:
                _tmpfd, _tmppath = None, None
                try:
                    _tmpfd, _tmppath = _tempfile.mkstemp(
                        dir=_os.path.dirname(rp), suffix='.autobe_tmp')
                    _os.close(_tmpfd)
                    _tmpfd = None
                    with _zipfile.ZipFile(rp, 'r') as zin:
                        with _zipfile.ZipFile(_tmppath, 'w', _zipfile.ZIP_DEFLATED) as zout:
                            written = set()
                            for item in zin.infolist():
                                if item.filename in serialised:
                                    zout.writestr(item, serialised[item.filename])
                                    written.add(item.filename)
                                elif item.filename in serialised_bin:
                                    zout.writestr(item, serialised_bin[item.filename])
                                    written.add(item.filename)
                                else:
                                    zout.writestr(item, zin.read(item.filename))
                            # Add any files that existed in other groups but not this one
                            for ui_path, content in serialised.items():
                                if ui_path not in written:
                                    zout.writestr(ui_path, content)
                            for ui_path, content in serialised_bin.items():
                                if ui_path not in written:
                                    zout.writestr(ui_path, content)
                    _os.replace(_tmppath, rp)
                    _tmppath = None
                except Exception:
                    pass
                finally:
                    if _tmpfd is not None:
                        try:
                            _os.close(_tmpfd)
                        except Exception:
                            pass
                    if _tmppath and _os.path.exists(_tmppath):
                        try:
                            _os.unlink(_tmppath)
                        except Exception:
                            pass
        except Exception:
            pass

    def _merge_subpack_hud_files(self, output_root):
        """For every subpack inside a merged RP that contains ui/hud_screen.json,
        merge the merged root hud_screen.json into that subpack file so selecting
        a subpack variant (e.g. SWAILA position) does not discard the merged root
        HUD patches (mqps bars, temperature overlay, Paraglider UI, …).

        Strategy: merged-root is the base; subpack changes are applied on top
        (last-wins for primitives so the subpack's positioning/visibility wins,
        first-seen entries for new keys).
        """
        try:
            for entry in _os.scandir(output_root):
                if not entry.is_dir():
                    continue
                rp = _os.path.join(entry.path, 'resource_pack.mcpack')
                if not _os.path.isfile(rp):
                    continue
                try:
                    with _zipfile.ZipFile(rp, 'r') as zf:
                        names = zf.namelist()
                        # Find root hud_screen
                        if 'ui/hud_screen.json' not in names:
                            continue
                        try:
                            root_hud = _json.loads(zf.read('ui/hud_screen.json'))
                        except Exception:
                            continue
                        # Find subpack hud_screen.json files
                        sub_hud_paths = [
                            n for n in names
                            if n.startswith('subpacks/') and n.endswith('/ui/hud_screen.json')
                        ]
                        if not sub_hud_paths:
                            continue
                        # Build merged subpack versions
                        merged_subs = {}
                        for sub_path in sub_hud_paths:
                            try:
                                sub_data = _json.loads(zf.read(sub_path))
                                import copy as _copy
                                combined = _copy.deepcopy(root_hud)
                                self._deep_merge_dicts(combined, sub_data,
                                                       _combine_visible=True)
                                merged_subs[sub_path] = _json.dumps(combined, indent=2,
                                                                     ensure_ascii=False)
                            except Exception:
                                pass
                        if not merged_subs:
                            continue
                    # Rewrite RP with updated subpack hud_screen files
                    _tmpfd, _tmppath = None, None
                    try:
                        _tmpfd, _tmppath = _tempfile.mkstemp(
                            dir=_os.path.dirname(rp), suffix='.autobe_tmp')
                        _os.close(_tmpfd)
                        _tmpfd = None
                        with _zipfile.ZipFile(rp, 'r') as zin:
                            with _zipfile.ZipFile(_tmppath, 'w',
                                                  _zipfile.ZIP_DEFLATED) as zout:
                                for item in zin.infolist():
                                    if item.filename in merged_subs:
                                        zout.writestr(item,
                                                      merged_subs[item.filename])
                                    else:
                                        zout.writestr(item,
                                                      zin.read(item.filename))
                        _os.replace(_tmppath, rp)
                        _tmppath = None
                    except Exception:
                        pass
                    finally:
                        if _tmpfd is not None:
                            try:
                                _os.close(_tmpfd)
                            except Exception:
                                pass
                        if _tmppath and _os.path.exists(_tmppath):
                            try:
                                _os.unlink(_tmppath)
                            except Exception:
                                pass
                except Exception:
                    pass
        except Exception:
            pass

    def _deep_merge_dicts(self, base, overlay, _combine_visible=False):
        """Recursively merge overlay into base in-place.
        Lists are replaced (not appended) to avoid duplicating UI element arrays.
        Exception: 'modifications' lists are concatenated so every pack's UI
        injection operations (insert_front/insert_after/etc.) are all preserved.
        When _combine_visible is True, 'visible' string values are combined with
        ' && ' instead of replaced, preserving each pack's UI visibility conditions.
        """
        for k, v in overlay.items():
            if k in base and isinstance(base[k], dict) and isinstance(v, dict):
                self._deep_merge_dicts(base[k], v, _combine_visible=_combine_visible)
            elif (_combine_visible and k == 'visible'
                  and isinstance(base.get(k), str) and isinstance(v, str)
                  and base[k] != v):
                base[k] = f'({base[k]}) && ({v})'
            elif (k == 'modifications'
                  and isinstance(base.get(k), list) and isinstance(v, list)):
                base[k] = base[k] + v
            else:
                base[k] = v

    def _extract_entity_identifier_from_json(self, data):
        """Return the identifier string from already-loaded entity JSON, or None."""
        for key in ('minecraft:entity', 'minecraft:client_entity'):
            if key in data:
                identifier = data[key].get('description', {}).get('identifier')
                if identifier and identifier != 'minecraft:player':
                    return identifier
        return None

    def _extract_item_identifier_from_json(self, data):
        """Return the identifier string from already-loaded item JSON, or None."""
        if 'minecraft:item' in data:
            return data['minecraft:item'].get('description', {}).get('identifier')
        return None

    def _extract_block_identifier_from_json(self, data):
        """Return the identifier string from already-loaded block JSON, or None."""
        if 'minecraft:block' in data:
            return data['minecraft:block'].get('description', {}).get('identifier')
        return None

    def _process_packs(self, _files, _output_dir):
        _output_zip_path_resource = _os.path.join(_output_dir, "resource_pack.zip")
        _output_zip_path_behavior = _os.path.join(_output_dir, "behavior_pack.zip")

        _json_contents_resource = {}
        _json_contents_behavior = {}
        _lang_contents_resource = {}
        _lang_contents_behavior = {}
        _material_contents = {}
        _mcfunction_contents = {}
        _written_feature_rules = {}  # basename -> arcname already written

        _text_json_contents_resource = {}
        # First-wins tracking for binary assets so earlier packs' textures/sounds are not
        # overwritten by later packs' files at the same path.
        _written_paths_resource = set()
        _written_paths_behavior = set()

        # Dictionary to store player-related JSON data
        _player_json_contents_resource = {}  # For resource packs (entity folder)
        _player_json_contents_behavior = {}  # For behavior packs (entities folder)
        
        # Dictionary to store entity files grouped by identifier for intelligent merging
        # Format: {identifier: {file_path: json_data}}
        _entity_files_by_identifier_resource = {}  # For resource packs (entity folder)
        _entity_files_by_identifier_behavior = {}  # For behavior packs (entities folder)
        
        # Dictionary to store item/block files grouped by identifier
        _item_files_by_identifier = {}  # For items
        _block_files_by_identifier = {}  # For blocks

        _mergeable_files = {
            "item_texture.json", "terrain_texture.json", "tick.json", "sounds.json", "blocks.json",
            "biomes_client.json", "sound_definitions.json", "music_definitions.json",
            "_ui_defs.json", "hud_screen.json", "npc_interact_screen.json", 
            "_global_variables.json", "ui_common.json", "splashes.json",
            "player.animation_controllers.json", "player.animation.json", "player.render_controllers.json",
            "crafting_item_catalog.json",
        }
        # List-type JSON files: arrays that must be union-merged rather than dict-merged
        _list_mergeable_files = {"flipbook_textures.json", "textures_list.json"}
        _list_json_contents_resource = {}   # path -> combined list entries

        # Initialize identifier conflict resolution system for universal addon compatibility
        identifier_manager = None
        try:
            identifier_manager = IdentifierManager()
            # First pass: Scan all packs for identifiers to detect conflicts
            all_pack_identifiers = {}
            for scan_file in _files:
                scan_file_path = scan_file
                if _os.path.isdir(scan_file_path):
                    # For directories, create a temp zip to scan
                    temp_zip_path = _os.path.join(_output_dir, f"temp_scan_{_os.path.basename(scan_file_path)}.mcpack")
                    with _zipfile.ZipFile(temp_zip_path, 'w', _zipfile.ZIP_DEFLATED) as zf:
                        for root, dirs, files in _os.walk(scan_file_path):
                            for file in files:
                                file_path = _os.path.join(root, file)
                                arcname = _os.path.relpath(file_path, scan_file_path)
                                zf.write(file_path, arcname)
                    scan_file_path = temp_zip_path
                
                try:
                    with _zipfile.ZipFile(scan_file_path, 'r') as scan_zip:
                        all_pack_identifiers[scan_file] = identifier_manager.scan_pack_identifiers(scan_zip, scan_file)
                except Exception as e:
                    _logging.warning(f"Could not scan identifiers from {scan_file}: {e}")
            
            # Detect conflicts; optionally show UI for user to choose which pack to keep per conflict
            if all_pack_identifiers:
                identifier_manager.detect_conflicts(all_pack_identifiers)
                conflict_list = identifier_manager.get_conflict_list()
                if conflict_list:
                    self._set_discord_merge_step(
                        f"Resolving {len(conflict_list)} conflict{'s' if len(conflict_list) != 1 else ''}",
                        "Waiting for user input"
                    )
                    _conflict_done = threading.Event()
                    def _show_conflict_ui():
                        self._show_conflict_resolution_overlay(conflict_list, identifier_manager, _conflict_done)
                    if threading.current_thread() is threading.main_thread():
                        _show_conflict_ui()
                    else:
                        self._root.after(0, _show_conflict_ui)
                        _conflict_done.wait()
                identifier_manager.generate_identifier_mappings()
                _logging.info(f"Identifier conflict resolution initialized: {len(identifier_manager.identifier_mapping)} mappings created")
        except Exception as e:
            _logging.warning(f"Identifier manager initialization failed (merging will continue without conflict resolution): {e}")
            identifier_manager = None

        self._progress['value'] = 0
        self._progress['maximum'] = 100  # always 0-100 so _update_progress percentages are correct

        _merge_start_ts = int(_datetime.datetime.now().timestamp())
        self._discord_merge_last_update = 0  # reset rate limiter so first pack always shows

        _total_files = len(_files)
        for _i, _file in enumerate(_files):
            # Update step label and progress bar for each pack (Step 2 occupies 25-50 range)
            _pack_label = _os.path.basename(_file).replace('_modified', '')
            if len(_pack_label) > 55:
                _pack_label = _pack_label[:52] + '...'
            _step2_pct = 25 + int((_i / max(_total_files, 1)) * 25)  # 25% -> 50%
            try:
                self._progress['value'] = _step2_pct
                self._progress_step_label.config(
                    text=f"Step 2/4: Processing {_i + 1}/{_total_files} — {_pack_label}")
                self._root.update_idletasks()
            except Exception:
                pass
            # Update Discord RPC with current pack (rate-limited to once per 15 s inside method)
            self._update_discord_merge_progress(_pack_label, _i + 1, _total_files, _merge_start_ts)

            # If _file is a folder, zip it up as a .mcpack and process as usual
            if _os.path.isdir(_file):
                # Only treat as a pack if manifest.json and pack_icon are at the root
                manifest_path = _os.path.join(_file, 'manifest.json')
                has_icon = any(_os.path.isfile(_os.path.join(_file, f'pack_icon{ext}')) for ext in ['.png', '.jpg', '.jpeg'])
                if not (_os.path.isfile(manifest_path) and has_icon):
                    _logging.warning(f"Skipping {_file} - not a valid pack folder.")
                    continue
                # Zip the folder into a temp .mcpack
                temp_mcpack = _os.path.join(_output_dir, f"temp_{_os.path.basename(_file)}.mcpack")
                with _zipfile.ZipFile(temp_mcpack, 'w', _zipfile.ZIP_DEFLATED) as zf:
                    for root, dirs, files in _os.walk(_file):
                        # If we find a subfolder named 'subpacks', copy it as-is (do not iterate into it for manifests/icons)
                        rel_root = _os.path.relpath(root, _file)
                        if rel_root == 'subpacks':
                            for subpack_name in dirs:
                                subpack_path = _os.path.join(root, subpack_name)
                                for sub_root, sub_dirs, sub_files in _os.walk(subpack_path):
                                    for sub_file in sub_files:
                                        abs_path = _os.path.join(sub_root, sub_file)
                                        arcname = _os.path.relpath(abs_path, _file)
                                        zf.write(abs_path, arcname)
                            # Skip further walk into subpacks
                            dirs.clear()
                        else:
                            for file in files:
                                abs_path = _os.path.join(root, file)
                                arcname = _os.path.relpath(abs_path, _file)
                                zf.write(abs_path, arcname)
                _file = temp_mcpack  # Now process as a .mcpack file

            _manifest_data = self._get_manifest_data(_file)
            if not _manifest_data:
                _logging.warning(f"Skipping {_file} - manifest.json not found or invalid.")
                continue

            _module_type = _manifest_data.get("modules", [{}])[0].get("type", "")

            with _zipfile.ZipFile(_file, 'r') as _pack_zip:
                _pack_names = _pack_zip.namelist()
                _has_r_prefix = any(name.startswith('R/') for name in _pack_names)
                _has_b_prefix = any(name.startswith('B/') for name in _pack_names)
                _is_mcaddon_layout = _has_r_prefix or _has_b_prefix

                # Normalise module type: map resource-like variants to "resources" and
                # behaviour-like variants to "data" so packs with non-standard types
                # (e.g. "client_data", "javascript", "") are never silently skipped.
                _resource_types = {"resources", "client_data"}
                _behavior_types = {"data", "script", "javascript", "data_driven"}
                if _module_type in _resource_types:
                    _module_type = "resources"
                elif _module_type in _behavior_types:
                    _module_type = "data"
                elif not _is_mcaddon_layout:
                    # Unknown type on a plain pack: try to infer from folder structure
                    _pack_has_textures = any(n.startswith('textures/') for n in _pack_names)
                    _pack_has_entities_bp = any(n.startswith('entities/') for n in _pack_names)
                    if _pack_has_textures and not _pack_has_entities_bp:
                        _module_type = "resources"
                        _logging.warning(f"Unknown module type '{_module_type}' in {_file} — treating as resources (has textures/).")
                    else:
                        _module_type = "data"
                        _logging.warning(f"Unknown module type in {_file} — treating as data.")
                # For mcaddon layout, default to resources so _output_zip is set
                if _is_mcaddon_layout and _module_type not in {"resources", "data"}:
                    _module_type = "resources"

                with _zipfile.ZipFile(_output_zip_path_resource, 'a') as _output_zip_resource, _zipfile.ZipFile(_output_zip_path_behavior, 'a') as _output_zip_behavior:
                    # ExtendedBE pack-level fixers: run once per source pack with full zip access.
                    # These can analyse cross-file relationships and inject brand-new files
                    # (e.g. missing block definitions, corrected manifests) into the merged output.
                    _ebe_pack_extra = {"rp": {}, "bp": {}}
                    _ebe_pack_on = (
                        _EXTENDEDBE_FIXERS and
                        getattr(getattr(self, 'extendedbe_enabled_var', None), 'get', lambda: False)()
                    )
                    if _ebe_pack_on:
                        try:
                            _ebe_pack_extra = _extendedbe.apply_pack_fixers(
                                _EXTENDEDBE_FIXERS, _os.path.basename(_file), _pack_zip)
                        except Exception as _ebe_pe:
                            _logging.warning(f"[ExtendedBE] apply_pack_fixers error: {_ebe_pe}")
                    _last_ui_update = _time.monotonic()
                    _file_idx_in_pack = 0
                    for _item in _pack_zip.infolist():
                        _item_name = _item.filename
                        _file_idx_in_pack += 1
                        # Throttled UI refresh: update label every ~0.4 s so the user can see
                        # the app is alive even during long single-pack processing.
                        _now = _time.monotonic()
                        if _now - _last_ui_update >= 0.4:
                            _last_ui_update = _now
                            _short_name = _item_name if len(_item_name) <= 45 else '...' + _item_name[-42:]
                            try:
                                self._progress_step_label.config(
                                    text=f"Step 2/4: Pack {_i + 1}/{_total_files} — {_pack_label}\n↳ {_short_name}")
                                self._root.update_idletasks()
                            except Exception:
                                pass
                        _effective_module_type = _module_type
                        _output_zip = _output_zip_resource if _effective_module_type == "resources" else _output_zip_behavior

                        if _is_mcaddon_layout:
                            if _item_name.startswith('R/'):
                                _effective_module_type = "resources"
                                _output_zip = _output_zip_resource
                                _item_name = _item_name[2:]
                            elif _item_name.startswith('B/'):
                                _effective_module_type = "data"
                                _output_zip = _output_zip_behavior
                                _item_name = _item_name[2:]
                            else:
                                # Skip root-level files in mcaddon containers to avoid leaking R/B manifests into outputs
                                continue

                        # Skip source manifests and icons — the output pack gets its own generated manifest
                        _item_base_lower = _item_name.lower().split('/')[-1]
                        if _item_name.lower() == 'manifest.json' or _item_name.lower().endswith('/manifest.json'):
                            continue
                        if _item_base_lower in ('pack_icon.png', 'pack_icon.jpg', 'pack_icon.jpeg'):
                            continue
                        # Exclude ui/server_form.json from merged RPs.  Packs like BetterCombat
                        # ship a partial server_form.json that overrides vanilla form rendering
                        # but omits the 'long_form_panel' component, making all ActionFormData
                        # forms (including Lorewarden's menus) show only a dark background with
                        # no content.  The vanilla game engine has a complete built-in version;
                        # removing custom overrides lets all server UI forms render correctly.
                        if _effective_module_type == 'resources' and _item_base_lower == 'server_form.json':
                            continue

                        # If this is a subpacks/ file or folder, just copy as-is, do not process for manifests/icons
                        if _item_name.startswith('subpacks/'):
                            self._copy_to_zip(_pack_zip, _item, _output_zip, None, _file, identifier_manager, _override_name=_item_name,
                                              _written_paths=_written_paths_resource if _output_zip is _output_zip_resource else _written_paths_behavior)
                            continue
                        if _item_name.startswith("feature_rules"):
                            _fr_base = _os.path.basename(_item_name)
                            if _fr_base and not _fr_base.endswith('/'):
                                if _fr_base not in _written_feature_rules:
                                    _fr_arc = f"feature_rules/{_fr_base}"
                                    _written_feature_rules[_fr_base] = _fr_arc
                                else:
                                    # Collision: prefix with a short pack token to keep both rules
                                    _fr_tok = _re.sub(r'[^a-z0-9]', '', _os.path.basename(_file).lower())[:8]
                                    _fr_arc = f"feature_rules/{_fr_tok}_{_fr_base}"
                                with _pack_zip.open(_item) as _fr_data:
                                    _output_zip.writestr(_fr_arc, _fr_data.read())
                            continue
                        if _item_name.endswith(".json"):
                            if _effective_module_type == "resources" and _item_name.startswith("texts/"):
                                with _pack_zip.open(_item) as _json_file:
                                    try:
                                        _json_data = self._load_json_with_comments(_json_file)
                                        # Accept both dict (e.g. texts/en_US.json) and list
                                        # (e.g. texts/languages.json = ["en_US", ...]) so the
                                        # union-merge write loop actually processes them.
                                        if _json_data is not None:
                                            _text_json_contents_resource.setdefault(_item_name, []).append(_json_data)
                                            continue
                                    except Exception:
                                        pass
                            # Check if the JSON file is in the 'entity' or 'entities' folder
                            if _os.path.dirname(_item_name) in {"entity", "entities"}:
                                with _pack_zip.open(_item) as _json_file:
                                    try:
                                        _json_data = self._load_json_with_comments(_json_file)
                                        # Update identifiers in entity files if manager is available
                                        if identifier_manager:
                                            try:
                                                _json_data = identifier_manager.update_json_identifiers(_json_data, _file)
                                            except Exception as e:
                                                _logging.warning(f"Error updating entity identifiers in {_item_name}: {e}")
                                        # Check for 'minecraft:client_entity' -> 'description' -> 'identifier'
                                        client_entity = _json_data.get("minecraft:client_entity")
                                        if client_entity and isinstance(client_entity, dict):
                                            description = client_entity.get("description")
                                            if description and isinstance(description, dict):
                                                identifier = description.get("identifier")
                                                if identifier == "minecraft:player":
                                                    # Store player-related JSON data for merging
                                                    _player_json_contents_resource.setdefault(_item_name, []).append(_json_data)
                                                    continue  # Skip copying this file directly
                                    except _json.JSONDecodeError:
                                        _logging.warning(f"Failed to parse JSON file: {_item_name}")
                            # Handle other JSON files
                            if _os.path.basename(_item_name) not in _mergeable_files:
                                # For entity/item/block files, collect by identifier for intelligent merging
                                dir_name = _os.path.dirname(_item_name)
                                if dir_name in {"entities", "entity", "items", "blocks"}:
                                    try:
                                        with _pack_zip.open(_item) as _json_file:
                                            _json_data = self._load_json_with_comments(_json_file)
                                            # ExtendedBE: apply per-file fixer before identifier-based collection.
                                            # Entity/item/block files never reach _copy_to_zip so fixers must run here.
                                            if (_EXTENDEDBE_FIXERS and _file and
                                                    getattr(getattr(self, 'extendedbe_enabled_var', None), 'get', lambda: False)()):
                                                try:
                                                    _jb_id = _json.dumps(_json_data, indent=2).encode('utf-8')
                                                    _, _jb_id_out = _extendedbe.apply_fixers(
                                                        _EXTENDEDBE_FIXERS, _os.path.basename(_file), _item_name, _jb_id)
                                                    if _jb_id_out != _jb_id:
                                                        _json_data = _json.loads(_jb_id_out.decode('utf-8'))
                                                except Exception as _ebe_id_e:
                                                    _logging.warning(f"[ExtendedBE] fixer error on {_item_name}: {_ebe_id_e}")

                                            # Extract identifier BEFORE renaming (we need original identifier for grouping)
                                            # This allows us to merge entities with the same identifier
                                            if dir_name in {"entities", "entity"}:
                                                entity_id = self._extract_entity_identifier_from_json(_json_data)
                                                if entity_id:
                                                    if identifier_manager and not identifier_manager.should_include_definition(_file, entity_id):
                                                        continue  # User chose to keep another pack's definition
                                                    entity_dict = _entity_files_by_identifier_behavior if _effective_module_type in {"data", "script"} else _entity_files_by_identifier_resource
                                                    if entity_id not in entity_dict:
                                                        entity_dict[entity_id] = []
                                                    entity_dict[entity_id].append({
                                                        'file_path': _item_name,
                                                        'data': _json_data,
                                                        'pack_path': _file,
                                                        'original_id': entity_id
                                                    })
                                                    continue  # Skip copying - will be merged later
                                                else:
                                                    # No identifier — if it's player.json in a BP, accumulate for merge
                                                    if _os.path.basename(_item_name) == 'player.json' and _effective_module_type in {"data", "script"}:
                                                        _player_json_contents_behavior.setdefault(_item_name, []).append(_json_data)
                                                    else:
                                                        self._copy_to_zip(_pack_zip, _item, _output_zip, _json_data, _file, identifier_manager, _override_name=_item_name)
                                            elif dir_name == "items":
                                                item_id = self._extract_item_identifier_from_json(_json_data)
                                                if item_id:
                                                    if identifier_manager and not identifier_manager.should_include_definition(_file, item_id):
                                                        continue
                                                    if item_id not in _item_files_by_identifier:
                                                        _item_files_by_identifier[item_id] = []
                                                    _item_files_by_identifier[item_id].append({
                                                        'file_path': _item_name,
                                                        'data': _json_data,
                                                        'pack_path': _file,
                                                        'original_id': item_id
                                                    })
                                                    continue  # Skip copying - will be merged later
                                                else:
                                                    self._copy_to_zip(_pack_zip, _item, _output_zip, _json_data, _file, identifier_manager, _override_name=_item_name)
                                            elif dir_name == "blocks":
                                                block_id = self._extract_block_identifier_from_json(_json_data)
                                                if block_id:
                                                    if identifier_manager and not identifier_manager.should_include_definition(_file, block_id):
                                                        continue
                                                    if block_id not in _block_files_by_identifier:
                                                        _block_files_by_identifier[block_id] = []
                                                    _block_files_by_identifier[block_id].append({
                                                        'file_path': _item_name,
                                                        'data': _json_data,
                                                        'pack_path': _file,
                                                        'original_id': block_id
                                                    })
                                                    continue  # Skip copying - will be merged later
                                                else:
                                                    self._copy_to_zip(_pack_zip, _item, _output_zip, _json_data, _file, identifier_manager, _override_name=_item_name)
                                    except Exception as e:
                                        _logging.warning(f"Error processing {_item_name}: {e}")
                                        self._copy_to_zip(_pack_zip, _item, _output_zip, None, _file, identifier_manager, _override_name=_item_name,
                                                          _written_paths=_written_paths_resource if _output_zip is _output_zip_resource else _written_paths_behavior)
                                else:
                                    self._copy_to_zip(_pack_zip, _item, _output_zip, None, _file, identifier_manager, _override_name=_item_name,
                                                      _written_paths=_written_paths_resource if _output_zip is _output_zip_resource else _written_paths_behavior)
                            elif _os.path.basename(_item_name) in _list_mergeable_files and _effective_module_type == "resources":
                                # flipbook_textures.json / textures_list.json are top-level arrays;
                                # collect all entries for union merge instead of dict merge.
                                with _pack_zip.open(_item) as _jf:
                                    try:
                                        _jd = self._load_json_with_comments(_jf)
                                        if isinstance(_jd, list):
                                            _list_json_contents_resource.setdefault(_item_name, []).extend(_jd)
                                        elif isinstance(_jd, dict):
                                            self._handle_json_item(_pack_zip, _item, _json_contents_resource, _output_zip, _effective_module_type, _file, identifier_manager, _override_name=_item_name)
                                    except Exception:
                                        pass
                            else:
                                # ExtendedBE: run per-file fixers on mergeable files (sounds.json etc.)
                                # before they're collected for dict-merge, so invalid entries are removed
                                # from each source before they can pollute the merged output.
                                _ebe_mf_injected = False
                                if (_EXTENDEDBE_FIXERS and _file and
                                        getattr(getattr(self, 'extendedbe_enabled_var', None), 'get', lambda: False)()):
                                    try:
                                        with _pack_zip.open(_item) as _mf_fh:
                                            _mf_bytes = _mf_fh.read()
                                        _, _mf_fixed = _extendedbe.apply_fixers(
                                            _EXTENDEDBE_FIXERS, _os.path.basename(_file), _item_name, _mf_bytes)
                                        if _mf_fixed != _mf_bytes:
                                            _mf_fixed_json = _json.loads(_mf_fixed.decode('utf-8'))
                                            _collect = (_json_contents_resource if _effective_module_type == "resources"
                                                        else _json_contents_behavior)
                                            _collect.setdefault(_item_name, []).append(_mf_fixed_json)
                                            _ebe_mf_injected = True
                                    except Exception as _ebe_mfe:
                                        _logging.warning(f"[ExtendedBE] mergeable fixer error on {_item_name}: {_ebe_mfe}")
                                if not _ebe_mf_injected:
                                    self._handle_json_item(_pack_zip, _item,
                                        _json_contents_resource if _effective_module_type == "resources" else _json_contents_behavior,
                                        _output_zip, _effective_module_type, _file, identifier_manager, _override_name=_item_name)
                        elif _item_name.endswith(".lang"):
                            with _pack_zip.open(_item) as _lang_file:
                                _raw = _lang_file.read()
                                try:
                                    _lang_data = _raw.decode('utf-8')
                                except Exception:
                                    _lang_data = _raw.decode('latin-1', errors='ignore')
                                _lang_data = strip_bom(_lang_data)
                                # Apply identifier renames to lang keys so they stay in sync
                                if identifier_manager:
                                    try:
                                        _lang_data = identifier_manager.update_text_identifiers(_lang_data, _file)
                                    except Exception:
                                        pass
                                # Lang files always go into the resource pack regardless of pack type:
                                # Minecraft reads display-name translations from the RP.  Many addon
                                # creators only ship lang files inside their BP, so we mirror them to
                                # the RP as well to ensure names resolve in-game.
                                _lang_contents_resource.setdefault(_item_name, []).append(_lang_data)
                                # Also keep BP lang in the behavior pack for script access
                                if _effective_module_type in {"data", "script"}:
                                    _lang_contents_behavior.setdefault(_item_name, []).append(_lang_data)
                        elif _item_name.endswith(".material"):
                            self._handle_json_item(_pack_zip, _item, _material_contents, _output_zip, _effective_module_type, _file, identifier_manager)
                        elif _item_name.endswith(".mcfunction"):
                            with _pack_zip.open(_item) as _mcfunction_file:
                                try:
                                    _mcfunction_data = _mcfunction_file.read().decode('utf-8')
                                except UnicodeDecodeError:
                                    _mcfunction_data = _mcfunction_file.read().decode('latin-1')
                                _mcfunction_data = strip_bom(_mcfunction_data)
                                # Update identifiers in mcfunction files
                                if identifier_manager:
                                    try:
                                        _mcfunction_data = identifier_manager.update_text_identifiers(_mcfunction_data, _file)
                                    except Exception as e:
                                        _logging.warning(f"Error updating identifiers in {_item_name}: {e}")
                                _mcfunction_contents.setdefault(_item_name, []).append(_mcfunction_data)
                        else:
                            # Binary files: textures (.png), sounds (.ogg/.fsb), structures (.mcstructure),
                            # shaders, and any other non-text assets that don't need merging.
                            # First-wins: if two packs ship a file at the same path, keep the first.
                            self._copy_to_zip(
                                _pack_zip, _item, _output_zip, None, _file, identifier_manager,
                                _override_name=_item_name,
                                _written_paths=_written_paths_resource if _output_zip is _output_zip_resource else _written_paths_behavior)

                    # Write any new files injected by pack-level fixers.
                    for _xp, _xb in _ebe_pack_extra.get("rp", {}).items():
                        try:
                            _output_zip_resource.writestr(_xp, _xb)
                        except Exception as _xe:
                            _logging.warning(f"[ExtendedBE] failed to inject RP file {_xp}: {_xe}")
                    for _xp, _xb in _ebe_pack_extra.get("bp", {}).items():
                        try:
                            _output_zip_behavior.writestr(_xp, _xb)
                        except Exception as _xe:
                            _logging.warning(f"[ExtendedBE] failed to inject BP file {_xp}: {_xe}")

            self._progress['value'] = _i + 1
            try:
                self._root.update_idletasks()
            except Exception:
                pass

        if _list_json_contents_resource:
            with _zipfile.ZipFile(_output_zip_path_resource, 'a') as _output_zip:
                for _list_file, _list_entries in _list_json_contents_resource.items():
                    # Deduplicate by converting to a stable string key
                    _seen_keys = set()
                    _unique_entries = []
                    for _entry in _list_entries:
                        try:
                            _key = _json.dumps(_entry, sort_keys=True)
                        except Exception:
                            _key = str(_entry)
                        if _key not in _seen_keys:
                            _seen_keys.add(_key)
                            _unique_entries.append(_entry)
                    _output_zip.writestr(_list_file, _json.dumps(_unique_entries, indent=2, ensure_ascii=False))

        if _text_json_contents_resource:
            with _zipfile.ZipFile(_output_zip_path_resource, 'a') as _output_zip:
                for _json_file, _json_list in _text_json_contents_resource.items():
                    # Check if the data is list-based (e.g. texts/languages.json = ["en_US", ...])
                    _first_non_none = next((d for d in _json_list if d is not None), None)
                    if isinstance(_first_non_none, list):
                        # Union merge: collect all unique string entries across all packs
                        _merged_list = []
                        _seen_entries = set()
                        for _data in _json_list:
                            if not isinstance(_data, list):
                                continue
                            for _entry in _data:
                                if isinstance(_entry, str) and _entry not in _seen_entries:
                                    _merged_list.append(_entry)
                                    _seen_entries.add(_entry)
                        _output_zip.writestr(_json_file, _json.dumps(_merged_list, indent=2, ensure_ascii=False))
                    else:
                        _merged = {}
                        for _data in _json_list:
                            if not isinstance(_data, dict):
                                continue
                            for _k, _v in _data.items():
                                if _k not in _merged:
                                    _merged[_k] = _v
                        _output_zip.writestr(_json_file, _json.dumps(_merged, indent=2, ensure_ascii=False))

        # Vanilla player animation aliases used as a safe fallback baseline.
        # These are injected (setdefault) into the merged player entity so that
        # animation controllers which reference standard vanilla short names
        # (e.g. "crouch", "bob", "riding.arms") always resolve even when no
        # addon explicitly includes them in their player entity modifications.
        _VANILLA_PLAYER_ANIMS = {
            "root":                           "controller.animation.player.root",
            "move":                           "animation.player.move",
            "riding.arms":                    "animation.player.riding.arms",
            "riding.legs":                    "animation.player.riding.legs",
            "holding":                        "animation.player.holding",
            "brandish_spear":                 "animation.player.brandish_spear",
            "holding_spyglass":               "animation.player.holding_spyglass",
            "charging":                       "animation.player.charging",
            "attack.positions":               "animation.player.attack.positions",
            "attack.rotations":               "animation.player.attack.rotations",
            "sneaking":                       "animation.player.sneaking",
            "crouch":                         "animation.player.sneaking",
            "bob":                            "animation.player.bob",
            "damage_nearby_mobs":             "animation.player.damage_nearby_mobs",
            "fishing_rod":                    "animation.player.fishing_rod",
            "swimming":                       "animation.player.swimming",
            "swimming.legs":                  "animation.player.swimming.legs",
            "use_item_progress":              "animation.player.use_item_progress",
            "skeleton_attack":                "animation.player.skeleton_attack",
            "sleeping":                       "animation.player.sleeping",
            "cape":                           "animation.player.cape",
            "first_person_base_pose":         "animation.player.first_person_base_pose",
            "first_person_empty_hand":        "animation.player.first_person_empty_hand",
            "first_person_swap_item":         "animation.player.first_person_swap_item",
            "first_person_attack_controller": "controller.animation.player.first_person_attack",
            "first_person_map_controller":    "controller.animation.player.first_person_map",
            "first_person_crossbow_equipped": "animation.player.first_person_crossbow_equipped",
            "first_person_breathing_bob":     "animation.player.first_person_breathing_bob",
            "third_person_bow":               "animation.player.third_person_bow",
            "third_person_crossbow":          "animation.player.third_person_crossbow",
            "third_person_die":               "animation.player.third_person_die",
            "third_person_map_controller":    "controller.animation.player.third_person_map",
            "blink":                          "controller.animation.player.blink",
            "totem_animation":                "animation.player.totem",
            "totem_controller":               "controller.animation.player.totem",
            "look_at_target_ui":              "animation.player.look_at_target.ui",
            "look_at_target_default":         "animation.player.look_at_target.default",
            "look_at_target_gliding":         "animation.player.look_at_target.gliding",
            "look_at_target_swimming":        "animation.player.look_at_target.swimming",
            "look_at_target_inverted":        "animation.player.look_at_target.inverted",
        }

        # Scan ALL player-related animation/controller files for variables that are used but
        # never assigned.  Done unconditionally so the scan runs even when no pack in this
        # group supplies an entity/player.json (e.g. the 'none' group only has an RP half).
        _anim_var_undefined = set()
        _RUNTIME_VARS = {
            'is_holding_left': (
                'variable.is_holding_left = '
                '!query.is_item_name_any(\'slot.weapon.offhand\', 0, \'minecraft:air\');'
            ),
            'player_arm_height': 'variable.player_arm_height = 0.0;',
            'short_arm_offset_left': 'variable.short_arm_offset_left = 0.0;',
            'short_arm_offset_right': 'variable.short_arm_offset_right = 0.0;',
            'is_horizontal_splitscreen': 'variable.is_horizontal_splitscreen = 0.0;',
            'is_vertical_splitscreen': 'variable.is_vertical_splitscreen = 0.0;',
        }
        try:
            _anim_used = set()
            for _key, _datalist in _json_contents_resource.items():
                _is_player_anim = (
                    ('animation_controllers' in _key and 'player' in _key) or
                    ('animations' in _key and 'player' in _key and
                     not _key.endswith('_controllers.json'))
                )
                if not _is_player_anim:
                    continue
                _text = _json.dumps(_datalist)
                _anim_used.update(
                    _re.findall(r'variable\.([a-zA-Z_][a-zA-Z0-9_]*)', _text))
            # All used variables are candidates for injection; the _already filter
            # (built from the merged entity's actual initialize/pre_animation blocks)
            # is the correct gate — not _anim_assigned, which fires on assignments inside
            # animation states and incorrectly marks variables as "initialised".
            _anim_var_undefined = _anim_used
        except Exception:
            pass

        # Merge player-related JSON files for resource packs (entity folder)
        if _player_json_contents_resource:
            merged_player_data = {}
            for _item_name, _json_data_list in _player_json_contents_resource.items():
                for _json_data in _json_data_list:
                    self._merge_json_data(merged_player_data, _json_data)

            # Inject any undefined animation variables into the merged entity/player.json
            try:
                if _anim_var_undefined:
                    _desc = (merged_player_data
                             .setdefault('minecraft:client_entity', {})
                             .setdefault('description', {}))
                    _scripts = _desc.setdefault('scripts', {})
                    _init    = _scripts.setdefault('initialize', [])
                    _pre     = _scripts.setdefault('pre_animation', [])
                    _existing_text = (' '.join(str(x) for x in _init) + ' ' +
                                      ' '.join(str(x) for x in _pre))
                    _already = set(_re.findall(r'variable\.([a-zA-Z_][a-zA-Z0-9_]*)\s*=',
                                               _existing_text))
                    for _vname in sorted(_anim_var_undefined - _already):
                        if _vname in _RUNTIME_VARS:
                            _pre.append(_RUNTIME_VARS[_vname])
                        else:
                            _init.append(f"variable.{_vname} = 0.0;")
            except Exception:
                pass

            # ── Post-merge fixes on the merged RP player entity ──────────────
            # Each fix has its own try/except so one failure cannot silence the rest.
            _pe_desc = {}
            try:
                _pe_desc = (merged_player_data
                            .get('minecraft:client_entity', {})
                            .get('description', {}))
            except Exception:
                pass

            # 1. Sanitize known-bad Molang slot names.
            try:
                _BAD_SLOTS = {
                    "'slot.mainhand'":         "'slot.weapon.mainhand'",
                    '"slot.mainhand"':         '"slot.weapon.mainhand"',
                    "'slot.offhand'":          "'slot.weapon.offhand'",
                    '"slot.offhand"':          '"slot.weapon.offhand"',
                }
                for _sblk in ('initialize', 'pre_animation'):
                    _slist = _pe_desc.get('scripts', {}).get(_sblk, [])
                    if not isinstance(_slist, list):
                        continue
                    for _si, _sexpr in enumerate(_slist):
                        if isinstance(_sexpr, str):
                            for _bad, _good in _BAD_SLOTS.items():
                                _sexpr = _sexpr.replace(_bad, _good)
                            _slist[_si] = _sexpr
            except Exception:
                pass

            # 2. Move entity-context queries out of 'initialize' into 'pre_animation'.
            #    query.is_item_name_any / query.property / query.equipped_item_any_tag
            #    all require entity context that initialize does not have.
            try:
                _ENTITY_CTX_QUERIES = (
                    'query.is_item_name_any',
                    'query.is_item_any_tag',
                    'query.equipped_item_any_tag',
                    'query.property(',
                    'query.has_equippable(',
                    'query.get_equipped_item_name(',
                )
                _scripts_dict  = _pe_desc.setdefault('scripts', {})
                _init_list_raw = _scripts_dict.get('initialize', [])
                _init_list     = list(_init_list_raw) if isinstance(_init_list_raw, list) else []
                _pre_list      = _scripts_dict.setdefault('pre_animation', [])
                if not isinstance(_pre_list, list):
                    _pre_list = []
                    _scripts_dict['pre_animation'] = _pre_list
                _keep_init, _move_to_pre = [], []
                for _expr in _init_list:
                    if isinstance(_expr, str) and any(q in _expr for q in _ENTITY_CTX_QUERIES):
                        _move_to_pre.append(_expr)
                    else:
                        _keep_init.append(_expr)
                if _move_to_pre:
                    _scripts_dict['initialize'] = _keep_init
                    _existing_pre_text = ' '.join(str(x) for x in _pre_list)
                    for _mv in _move_to_pre:
                        if _mv not in _existing_pre_text:
                            _pre_list.append(_mv)
            except Exception:
                pass

            # 3. Backfill missing vanilla animation aliases.
            try:
                _anims_dict = _pe_desc.setdefault('animations', {})
                if not isinstance(_anims_dict, dict):
                    _anims_dict = {}
                    _pe_desc['animations'] = _anims_dict
                for _alias, _anim_id in _VANILLA_PLAYER_ANIMS.items():
                    _anims_dict.setdefault(_alias, _anim_id)
            except Exception:
                pass

            # 4. Stub any animation short-names in scripts.animate that are not
            #    defined in the merged animations dict.
            try:
                _animate_block = _pe_desc.get('scripts', {}).get('animate', [])
                if not isinstance(_animate_block, list):
                    _animate_block = []
                _defined_aliases = set(_anims_dict.keys()) if isinstance(_anims_dict, dict) else set()
                for _entry in _animate_block:
                    _aname = None
                    if isinstance(_entry, str):
                        _aname = _entry.strip()
                    elif isinstance(_entry, dict):
                        _aname = next(iter(_entry), None)
                    if _aname and _aname not in _defined_aliases:
                        _anims_dict[_aname] = "animation.player.move"
                        _defined_aliases.add(_aname)
            except Exception:
                pass

            # 5. De-duplicate scripts.animate by name (dict-with-condition beats plain string).
            try:
                _scripts_blk = _pe_desc.get('scripts', {})
                _anim_blk2 = _scripts_blk.get('animate', [])
                if isinstance(_anim_blk2, list):
                    _anim_seen2 = {}
                    for _ae2 in _anim_blk2:
                        if isinstance(_ae2, str):
                            if _ae2 not in _anim_seen2:
                                _anim_seen2[_ae2] = _ae2
                        elif isinstance(_ae2, dict) and _ae2:
                            _ak2 = next(iter(_ae2))
                            _anim_seen2[_ak2] = _ae2  # dict wins over any earlier plain string
                    _scripts_blk['animate'] = list(_anim_seen2.values())
            except Exception:
                pass

            # 6. De-duplicate render_controllers by controller name (first occurrence wins).
            try:
                _rc_list2 = _pe_desc.get('render_controllers', [])
                if isinstance(_rc_list2, list):
                    _rc_seen2 = {}
                    for _rce2 in _rc_list2:
                        if isinstance(_rce2, dict) and _rce2:
                            _rcn2 = next(iter(_rce2))
                            if _rcn2 not in _rc_seen2:
                                _rc_seen2[_rcn2] = _rce2
                        elif isinstance(_rce2, str) and _rce2 not in _rc_seen2:
                            _rc_seen2[_rce2] = _rce2
                    _pe_desc['render_controllers'] = list(_rc_seen2.values())
            except Exception:
                pass

            with _zipfile.ZipFile(_output_zip_path_resource, 'a') as _output_zip:
                _output_zip.writestr("entity/player.entity.json", _json.dumps(merged_player_data, indent=2))
        

        if _anim_var_undefined:
            # No pack in this group supplied an entity/player.json but animation controllers
            # reference uninitialized variables.  Write a minimal client-entity stub so
            # Molang doesn't error on the first frame.
            try:
                _stub_init = []
                _stub_pre  = []
                for _vname in sorted(_anim_var_undefined):
                    if _vname in _RUNTIME_VARS:
                        _stub_pre.append(_RUNTIME_VARS[_vname])
                    else:
                        _stub_init.append(f"variable.{_vname} = 0.0;")
                _stub = {
                    "format_version": "1.10.0",
                    "minecraft:client_entity": {
                        "description": {
                            "identifier": "minecraft:player",
                            "animations": dict(_VANILLA_PLAYER_ANIMS),
                            "scripts": {}
                        }
                    }
                }
                _stub_scripts = _stub["minecraft:client_entity"]["description"]["scripts"]
                if _stub_init:
                    _stub_scripts["initialize"] = _stub_init
                if _stub_pre:
                    _stub_scripts["pre_animation"] = _stub_pre
                with _zipfile.ZipFile(_output_zip_path_resource, 'a') as _output_zip:
                    _output_zip.writestr("entity/player.entity.json", _json.dumps(_stub, indent=2))
            except Exception:
                pass

        # Merge player-related JSON files for behavior packs (entities folder)
        if _player_json_contents_behavior:
            merged_player_data = {}
            for _item_name, _json_data_list in _player_json_contents_behavior.items():
                for _json_data in _json_data_list:
                    self._merge_json_data(merged_player_data, _json_data)
            with _zipfile.ZipFile(_output_zip_path_behavior, 'a') as _output_zip:
                _output_zip.writestr("entities/player.json", _json.dumps(merged_player_data, indent=2))
        
        # Merge entity files by identifier (intelligent merging - same entity from multiple addons)
        # IMPORTANT: When merging entities with the same identifier, we keep the original identifier
        # and merge their components. We only rename identifiers if they're different entities.
        
        # Resource packs (entity folder)
        with _zipfile.ZipFile(_output_zip_path_resource, 'a') as _output_zip:
            for entity_id, entity_list in _entity_files_by_identifier_resource.items():
                if len(entity_list) > 1:
                    # Multiple addons modify same entity - merge them intelligently
                    # Keep the original identifier (don't rename when merging)
                    merged_entity = {}
                    for entity_file in entity_list:
                        # Merge data from each addon
                        self._merge_json_data(merged_entity, entity_file['data'])
                    # Ensure the merged entity keeps the original identifier
                    if 'minecraft:client_entity' in merged_entity:
                        if 'description' not in merged_entity['minecraft:client_entity']:
                            merged_entity['minecraft:client_entity']['description'] = {}
                        desc = merged_entity['minecraft:client_entity']['description']
                        desc['identifier'] = entity_id
                        # Sanitize geometry/textures/materials: remove empty-string keys or values
                        # that can appear after merging and produce Molang 'geometry.default not found'
                        for _alias_key in ('geometry', 'textures', 'materials'):
                            if _alias_key in desc and isinstance(desc[_alias_key], dict):
                                desc[_alias_key] = {
                                    k: v for k, v in desc[_alias_key].items()
                                    if k and v and str(k).strip() and str(v).strip()
                                }
                    # Use the first file's path as the output path
                    output_path = entity_list[0]['file_path']
                    _output_zip.writestr(output_path, _json.dumps(merged_entity, indent=2))
                else:
                    # Only one addon modifies this entity
                    # Check if identifier needs renaming (different entity with same identifier)
                    entity_file = entity_list[0]
                    final_data = entity_file['data']
                    # Only rename if IdentifierManager says to (for different entities with same ID)
                    if identifier_manager and identifier_manager.should_rename_identifier(entity_file['original_id']):
                        final_data = identifier_manager.update_json_identifiers(final_data, entity_file['pack_path'])
                    _output_zip.writestr(entity_file['file_path'], _json.dumps(final_data, indent=2))
        
        # Behavior packs (entities folder)
        with _zipfile.ZipFile(_output_zip_path_behavior, 'a') as _output_zip:
            for entity_id, entity_list in _entity_files_by_identifier_behavior.items():
                if len(entity_list) > 1:
                    # Multiple addons modify same entity — use component-group routing for conflicts
                    merged_entity = self._merge_behavior_entity(entity_list)
                    # Ensure the merged entity keeps the original identifier
                    if 'minecraft:entity' in merged_entity:
                        if 'description' not in merged_entity['minecraft:entity']:
                            merged_entity['minecraft:entity']['description'] = {}
                        merged_entity['minecraft:entity']['description']['identifier'] = entity_id
                    output_path = entity_list[0]['file_path']
                    _output_zip.writestr(output_path, _json.dumps(merged_entity, indent=2))
                else:
                    entity_file = entity_list[0]
                    final_data = entity_file['data']
                    if identifier_manager and identifier_manager.should_rename_identifier(entity_file['original_id']):
                        final_data = identifier_manager.update_json_identifiers(final_data, entity_file['pack_path'])
                    _output_zip.writestr(entity_file['file_path'], _json.dumps(final_data, indent=2))
        
        # Merge item files by identifier
        with _zipfile.ZipFile(_output_zip_path_behavior, 'a') as _output_zip:
            for item_id, item_list in _item_files_by_identifier.items():
                if len(item_list) > 1:
                    # Multiple addons modify same item - merge them, keep original identifier
                    merged_item = {}
                    for item_file in item_list:
                        self._merge_json_data(merged_item, item_file['data'])
                    if 'minecraft:item' in merged_item:
                        if 'description' not in merged_item['minecraft:item']:
                            merged_item['minecraft:item']['description'] = {}
                        merged_item['minecraft:item']['description']['identifier'] = item_id
                    output_path = item_list[0]['file_path']
                    _output_zip.writestr(output_path, _json.dumps(merged_item, indent=2))
                else:
                    item_file = item_list[0]
                    final_data = item_file['data']
                    if identifier_manager and identifier_manager.should_rename_identifier(item_file['original_id']):
                        final_data = identifier_manager.update_json_identifiers(final_data, item_file['pack_path'])
                    _output_zip.writestr(item_file['file_path'], _json.dumps(final_data, indent=2))
        
        # Merge block files by identifier
        with _zipfile.ZipFile(_output_zip_path_behavior, 'a') as _output_zip:
            for block_id, block_list in _block_files_by_identifier.items():
                if len(block_list) > 1:
                    # Multiple addons modify same block - merge them, keep original identifier
                    merged_block = {}
                    for block_file in block_list:
                        self._merge_json_data(merged_block, block_file['data'])
                    if 'minecraft:block' in merged_block:
                        if 'description' not in merged_block['minecraft:block']:
                            merged_block['minecraft:block']['description'] = {}
                        merged_block['minecraft:block']['description']['identifier'] = block_id
                    output_path = block_list[0]['file_path']
                    _output_zip.writestr(output_path, _json.dumps(merged_block, indent=2))
                else:
                    block_file = block_list[0]
                    final_data = block_file['data']
                    if identifier_manager and identifier_manager.should_rename_identifier(block_file['original_id']):
                        final_data = identifier_manager.update_json_identifiers(final_data, block_file['pack_path'])
                    _output_zip.writestr(block_file['file_path'], _json.dumps(final_data, indent=2))

        # Merge other JSON, .lang, .material, and .mcfunction files
        self._merge_and_write_files(_json_contents_resource, _output_zip_path_resource)
        self._merge_and_write_files(_json_contents_behavior, _output_zip_path_behavior)
        self._merge_and_write_lang_files(_lang_contents_resource, _output_zip_path_resource)
        self._merge_and_write_lang_files(_lang_contents_behavior, _output_zip_path_behavior)
        self._merge_and_write_material_files(_material_contents, _output_zip_path_resource)
        self._merge_and_write_mcfunction_files(_mcfunction_contents, _output_zip_path_behavior)

        self._remove_empty_files(_output_zip_path_resource)
        self._remove_empty_files(_output_zip_path_behavior)

    def _merge_behavior_entity(self, entity_list):
        """
        Merge multiple behavior-pack definitions of the same entity.

        Strategy for root `components` conflicts:
          - First addon's value is kept as the base.
          - Each subsequent addon's *conflicting* component is placed into a uniquely-named
            component_group (`autobe_<packname>_ov`) and that group is activated via the
            `minecraft:entity_spawned` event.  This means ALL addons' component values are
            present in the file and Bedrock applies them in component-group stack order —
            fully deterministic, no silent drops.
          - Non-conflicting components are merged into the base directly.
        Everything outside `components` (component_groups, events, description, animations,
        scripts, …) is union-merged as usual.
        """
        if not entity_list:
            return {}
        if len(entity_list) == 1:
            return entity_list[0]['data']

        merged = {}
        self._merge_json_data(merged, entity_list[0]['data'])

        for entity_file in entity_list[1:]:
            src = entity_file['data']
            pack_raw = _os.path.basename(entity_file['pack_path'])
            pack_raw = _re.sub(r'\.(mcpack|mcaddon)$', '', pack_raw, flags=_re.IGNORECASE)
            pack_raw = _re.sub(r'_modified$', '', pack_raw, flags=_re.IGNORECASE)
            pack_raw = _re.sub(r'_\d+$', '', pack_raw)
            clean = _re.sub(r'[^a-zA-Z0-9]', '_', pack_raw)[:16].strip('_')
            group_name = f"autobe_{clean}_ov"

            ent_key = 'minecraft:entity'
            if ent_key not in src or ent_key not in merged:
                self._merge_json_data(merged, src)
                continue

            src_def = src[ent_key]
            base_def = merged[ent_key]
            src_comps = src_def.get('components', {})
            base_comps = base_def.setdefault('components', {})

            overrides = {}
            for comp_key, comp_val in src_comps.items():
                if comp_key in base_comps:
                    if _json.dumps(comp_val, sort_keys=True) != _json.dumps(base_comps[comp_key], sort_keys=True):
                        # Genuinely different value — route to component group
                        overrides[comp_key] = comp_val
                    # else: identical, skip
                else:
                    base_comps[comp_key] = comp_val  # new component, add to base

            if overrides:
                base_def.setdefault('component_groups', {})[group_name] = overrides
                spawn_ev = base_def.setdefault('events', {}).setdefault('minecraft:entity_spawned', {})
                cg_list = spawn_ev.setdefault('add', {}).setdefault('component_groups', [])
                if group_name not in cg_list:
                    cg_list.append(group_name)

            # Merge everything else in the entity definition except components (already handled)
            for k, v in src_def.items():
                if k == 'components':
                    continue
                if k in base_def:
                    if isinstance(base_def[k], dict) and isinstance(v, dict):
                        self._merge_json_data(base_def[k], v)
                    elif isinstance(base_def[k], list) and isinstance(v, list):
                        base_def[k] = self._union_merge_list(base_def[k], v)
                else:
                    base_def[k] = v

            # Merge top-level keys outside minecraft:entity
            for k, v in src.items():
                if k == ent_key:
                    continue
                if k not in merged:
                    merged[k] = v

        return merged

    # Numeric keys where "take the max" is the safest strategy when two addons conflict
    _MERGE_MAX_KEYS = frozenset({
        'value', 'max', 'min', 'amount', 'speed', 'damage',
        'range', 'radius', 'duration', 'cooldown', 'max_dist',
        'priority',  # lower priority number = higher priority; max keeps the less aggressive override
    })
    # Keys whose list values must always be union-deduplicated (order preserved)
    _UNION_LIST_KEYS = frozenset({
        'component_groups', 'animations', 'animate', 'particle_effects',
        'sound_effects', 'scripts', 'pools', 'entries', 'conditions',
        'spawn_rules', 'behaviors', 'render_controllers',
    })

    @staticmethod
    def _union_merge_list(existing, incoming):
        """Return existing + any items from incoming not already present (by JSON fingerprint)."""
        seen = {_json.dumps(i, sort_keys=True) if isinstance(i, (dict, list)) else str(i) for i in existing}
        result = list(existing)
        for item in incoming:
            key = _json.dumps(item, sort_keys=True) if isinstance(item, (dict, list)) else str(item)
            if key not in seen:
                result.append(item)
                seen.add(key)
        return result

    def _merge_json_data(self, target, source):
        """
        Recursively merges JSON data from `source` into `target` with intelligent conflict resolution.
        Handles entity files, player.json, and other common conflict scenarios.
        """
        for key, value in source.items():
            if key not in target:
                target[key] = value
                continue

            t = target[key]

            # Dicts always recurse
            if isinstance(t, dict) and isinstance(value, dict):
                self._merge_json_data(t, value)

            # Lists — union-deduplicate known union keys; extend others
            elif isinstance(t, list) and isinstance(value, list):
                if key in self._UNION_LIST_KEYS:
                    target[key] = self._union_merge_list(t, value)
                else:
                    target[key] = self._union_merge_list(t, value)

            # Primitive vs primitive
            else:
                if key in ('format_version', 'description', 'identifier'):
                    pass  # keep first
                elif key in self._MERGE_MAX_KEYS and isinstance(t, (int, float)) and isinstance(value, (int, float)):
                    # Two addons set the same stat differently — honour both by taking the larger value
                    target[key] = max(t, value)
                else:
                    target[key] = value  # last-wins for everything else

    def _copy_to_zip(self, _pack_zip, _item, _output_zip, _json_data=None, _pack_path=None, _identifier_manager=None, _override_name=None, _written_paths=None):
        _out_name = _override_name if _override_name else _item.filename
        # First-wins for binary assets: skip if this path was already written by an earlier pack
        if _written_paths is not None and _json_data is None:
            if _out_name in _written_paths:
                return
            _written_paths.add(_out_name)
        with _pack_zip.open(_item) as _file_data:
            if _json_data is not None:
                # If identifier manager is provided, update identifiers in JSON data
                if _identifier_manager and _pack_path:
                    try:
                        _json_data = _identifier_manager.update_json_identifiers(_json_data, _pack_path)
                    except Exception as e:
                        _logging.warning(f"Error updating identifiers in {_item.filename}: {e}")
                # ExtendedBE: run per-file fixers on pre-parsed JSON files too.
                # Entity behavior, recipe, sounds.json etc. all arrive here as dicts —
                # fixers never reached them before because they were in the else branch.
                _ebe_on_json = (
                    _EXTENDEDBE_FIXERS and _pack_path and
                    getattr(getattr(self, 'extendedbe_enabled_var', None), 'get', lambda: False)()
                )
                if _ebe_on_json:
                    try:
                        _jb_in = _json.dumps(_json_data, indent=2).encode('utf-8')
                        _ebe_path2, _jb_out = _extendedbe.apply_fixers(
                            _EXTENDEDBE_FIXERS, _os.path.basename(_pack_path), _out_name, _jb_in)
                        if _ebe_path2 != _out_name:
                            _out_name = _ebe_path2
                        if _jb_out != _jb_in:
                            try:
                                _json_data = _json.loads(_jb_out.decode('utf-8'))
                            except Exception:
                                pass
                    except Exception as _ebe_je:
                        _logging.warning(f"[ExtendedBE] JSON fixer error on {_out_name}: {_ebe_je}")
                _output_zip.writestr(_out_name, _json.dumps(_json_data, indent=2))
            else:
                file_data = _file_data.read()
                # ExtendedBE: apply per-addon fixers (broken/outdated addon patches).
                # Only runs when the user has enabled it in Settings → ExtendedBE Addon Fixer.
                _ebe_on = (
                    _EXTENDEDBE_FIXERS and _pack_path and
                    getattr(getattr(self, 'extendedbe_enabled_var', None), 'get', lambda: False)()
                )
                if _ebe_on:
                    try:
                        _pack_basename = _os.path.basename(_pack_path)
                        _ebe_path, file_data = _extendedbe.apply_fixers(
                            _EXTENDEDBE_FIXERS, _pack_basename, _out_name, file_data)
                        if _ebe_path != _out_name:
                            _out_name = _ebe_path  # fixer moved the file to a new path
                    except Exception as _ebe_err:
                        _logging.warning(f"[ExtendedBE] apply_fixers error on {_out_name}: {_ebe_err}")
                # Update identifiers in text-based files (scripts, etc.)
                if _identifier_manager and _pack_path and _out_name.endswith(('.js', '.mcfunction', '.lang')):
                    try:
                        text_content = file_data.decode('utf-8', errors='ignore')
                        updated_text = _identifier_manager.update_text_identifiers(text_content, _pack_path)
                        file_data = updated_text.encode('utf-8')
                    except Exception as e:
                        _logging.warning(f"Error updating identifiers in {_item.filename}: {e}")
                # JS compatibility patches — run unconditionally so they are never
                # silently skipped if the identifier-manager step throws above.
                if _out_name.endswith('.js'):
                    try:
                        js_text = file_data.decode('utf-8', errors='ignore')
                        # Strip bare empty action-bar clears (setActionBar("") / setActionBar(''))
                        # that silence other addons' HUD channels in merged packs.
                        # e.g. SWAILA clears with "" every 10 ticks, wiping MQPS's 'mqps...'
                        # bar data. Bedrock's natural fade + MQPS's next update handle cleanup.
                        js_text = _re.sub(
                            r'(?:[A-Za-z_$][\w$]*\.)+setActionBar\s*\(\s*(?:\'\'|"")\s*\)',
                            '(0)',
                            js_text
                        )
                        # Stagger entity-detecting scripts (SWAILA-like) from 10 → 25 ticks.
                        # MQPS runs every 10 ticks; LCM(10,25)=50 ticks before they align.
                        # SWAILA's setActionBar calls overwrite MQPS's data ~20% of the time
                        # instead of ~50% with 10→11, reducing visible flicker of MQPS bars.
                        if 'getEntitiesFromViewDirection' in js_text:
                            js_text = js_text.replace('}, 10);', '}, 25);')
                        file_data = js_text.encode('utf-8')
                    except Exception as e:
                        _logging.warning(f"Error applying JS compat patches in {_item.filename}: {e}")
                _output_zip.writestr(_out_name, file_data)

    def _handle_json_item(self, _pack_zip, _item, _json_contents, _output_zip, _module_type=None, _pack_path=None, _identifier_manager=None, _override_name=None):
        with _pack_zip.open(_item) as _json_file:
            try:
                _json_data = self._load_json_with_comments(_json_file)
                if isinstance(_json_data, dict):
                    # Update identifiers before storing for merging
                    if _identifier_manager and _pack_path:
                        try:
                            _json_data = _identifier_manager.update_json_identifiers(_json_data, _pack_path)
                        except Exception as e:
                            _logging.warning(f"Error updating identifiers in {_item.filename}: {e}")
                    _json_name = _override_name if _override_name else _item.filename
                    _json_contents.setdefault(_json_name, []).append(_json_data)
                else:
                    # Parser returned None or a non-dict (list, etc.) — fall back to raw copy so
                    # the file is not silently lost. The merged version (if any) is written later
                    # and will be the last entry in the zip, so it takes precedence.
                    self._copy_to_zip(_pack_zip, _item, _output_zip, None, _pack_path, _identifier_manager, _override_name=_override_name)
            except Exception:
                # Catch all parse/decode errors — not just JSONDecodeError — so a file is never
                # silently dropped. Raw copy ensures textures/sounds are still present in output.
                self._copy_to_zip(_pack_zip, _item, _output_zip, None, _pack_path, _identifier_manager, _override_name=_override_name)

    def _merge_and_write_files(self, _json_contents, _output_zip_path):
        for _json_file, _json_list in _json_contents.items():
            _merged_content = self._merge_json(_json_list, _os.path.basename(_json_file))
            with _zipfile.ZipFile(_output_zip_path, 'a') as _output_zip:
                _output_zip.writestr(_json_file, _json.dumps(_merged_content, indent=2))

    def _merge_and_write_lang_files(self, _lang_contents, _output_zip_path):
        for _lang_file, _lang_list in _lang_contents.items():
            _merged_lang_content = self._merge_lang_files(_lang_list)
            with _zipfile.ZipFile(_output_zip_path, 'a') as _output_zip:
                _output_zip.writestr(_lang_file, _merged_lang_content)

    def _merge_and_write_material_files(self, _material_contents, _output_zip_path):
        for _material_file, _material_list in _material_contents.items():
            _merged_material_content = self._merge_json(_material_list, _os.path.basename(_material_file))
            with _zipfile.ZipFile(_output_zip_path, 'a') as _output_zip:
                _output_zip.writestr(_material_file, _json.dumps(_merged_material_content, indent=2))

    def _merge_and_write_mcfunction_files(self, _mcfunction_contents, _output_zip_path):
        for _mcfunction_file, _mcfunction_list in _mcfunction_contents.items():
            _merged_mcfunction_content = "\n".join(strip_bom(x) for x in _mcfunction_list)
            _merged_mcfunction_content = strip_bom(_merged_mcfunction_content)
            with _zipfile.ZipFile(_output_zip_path, 'a') as _output_zip:
                _output_zip.writestr(_mcfunction_file, _merged_mcfunction_content)

    def _remove_empty_files(self, _zip_path):
        with _zipfile.ZipFile(_zip_path, 'r') as _zip:
            file_list = _zip.infolist()
            temp_file_path = _zip_path + ".temp"
            with _zipfile.ZipFile(temp_file_path, 'w') as temp_zip:
                for file in file_list:
                    if file.file_size > 0:
                        temp_zip.writestr(file, _zip.read(file.filename))

        _os.remove(_zip_path)
        _os.rename(temp_file_path, _zip_path)

    def _validate_pack_zip(self, _zip_path, _pack_kind):
        report = {
            "pack_kind": _pack_kind,
            "zip_path": _os.path.abspath(_zip_path),
            "exists": _os.path.exists(_zip_path),
            "leaked_prefix_paths": [],
            "has_manifest": False,
            "texts": {
                "has_en_us_lang": False,
                "has_en_us_json": False,
                "has_languages_json": False,
                "has_language_names_json": False,
            },
        }

        if not report["exists"]:
            return report

        try:
            with _zipfile.ZipFile(_zip_path, 'r') as zf:
                names = zf.namelist()
                report["has_manifest"] = any(n.lower().endswith('manifest.json') and '/' not in n.strip('/') for n in names)
                report["leaked_prefix_paths"] = [n for n in names if n.startswith('R/') or n.startswith('B/')]

                if _pack_kind == "resource":
                    report["texts"]["has_en_us_lang"] = any(n.lower() == 'texts/en_us.lang' for n in names)
                    report["texts"]["has_en_us_json"] = any(n.lower() == 'texts/en_us.json' for n in names)
                    report["texts"]["has_languages_json"] = any(n.lower() == 'texts/languages.json' for n in names)
                    report["texts"]["has_language_names_json"] = any(n.lower() == 'texts/language_names.json' for n in names)
        except Exception as e:
            report["error"] = str(e)

        return report

    def _write_merge_report(self, _output_dir, _bp_path, _rp_path, _source_packs):
        try:
            report = {
                "output_dir": _os.path.abspath(_output_dir),
                "source_packs": [_os.path.abspath(p) for p in _source_packs],
                "behavior_pack": self._validate_pack_zip(_bp_path, "behavior"),
                "resource_pack": self._validate_pack_zip(_rp_path, "resource"),
            }
            report_path = _os.path.join(_output_dir, "_autobe_merge_report.json")
            with open(report_path, 'w', encoding='utf-8') as f:
                _json.dump(report, f, indent=2)
        except Exception as e:
            _logging.warning(f"Could not write merge report: {e}")
    
    def _process_files(self, _selected_files):
        _imported_files = []

        _scripts_path = _os.path.join(self._out_dir, "scripts")

        # Ensure the scripts directory is empty or create it if it doesn't exist
        if _os.path.exists(_scripts_path):
            _shutil.rmtree(_scripts_path)
        _os.makedirs(_scripts_path, exist_ok=True)

        _main_js_path = _os.path.join(_scripts_path, "CodeNex.js")

        # Each pack gets its own isolated subdirectory under scripts/{pack_num}/
        # so that utility modules (utils.js, types.js, etc.) from different packs can
        # never overwrite each other.  Only the manifest entry file is renamed within
        # that directory; all other files keep their original names and relative imports
        # continue to resolve correctly because they share the same subdirectory.
        # _pack_info maps: mcpack_path -> (renamed_dict, pack_dir_path)
        _pack_info = {}

        for _mcpack_file in _selected_files:
            _pack_num  = _random.randint(10000, 99999)
            _pack_dir  = _os.path.join(_scripts_path, str(_pack_num))
            _renamed_in_pack = {}

            try:
                with _zipfile.ZipFile(_mcpack_file, 'r') as _zip_ref:
                    _namelist = _zip_ref.namelist()

                    # Collect script items from the two supported layouts
                    _script_items   = [n for n in _namelist
                                       if n.startswith('scripts/') and not n.endswith('/')]
                    _b_script_items = [n for n in _namelist
                                       if n.startswith('B/scripts/') and not n.endswith('/')]
                    _logging.info(f"[_process_files] {_os.path.basename(_mcpack_file)}: found {len(_script_items)} scripts, {len(_b_script_items)} B/scripts")

                    # Extract every script into this pack's isolated subdirectory,
                    # stripping the leading 'scripts/' (or 'B/scripts/') prefix.
                    # Apply JS compatibility patches (setActionBar stripping, tick stagger).
                    if _script_items or _b_script_items:
                        _os.makedirs(_pack_dir, exist_ok=True)
                        for _item in _script_items:
                            _rel = _item[len('scripts/'):]
                            if _rel:
                                _dest = _os.path.join(_pack_dir, _rel)
                                _os.makedirs(_os.path.dirname(_dest), exist_ok=True)
                                _js_bytes = _zip_ref.read(_item)
                                # Apply JS compatibility patches to any script
                                if _rel.endswith('.js'):
                                    _js_text = _js_bytes.decode('utf-8', errors='ignore')
                                    # Fix 1: Strip empty setActionBar calls (prevents wiping other addons' data)
                                    _js_text = __import__('re').sub(
                                        r'(?:[A-Za-z_$][\w$]*\.)+setActionBar\s*\(\s*(?:\'\'|"")\s*\)',
                                        '(0)',
                                        _js_text
                                    )
                                    # Detect if this script is an actionbar-heavy addon
                                    _uses_actionbar = 'setActionBar' in _js_text
                                    _is_mqps = 'mqps' in _js_text.lower() or 'more_hunger_bar' in _js_text
                                    _has_timer = any(x in _js_text for x in ['runInterval', 'setInterval', 'setTimeout', 'runTimeout'])
                                    
                                    # Fix 2: Stagger ANY timed actionbar script to reduce collisions
                                    if _uses_actionbar and _has_timer and '}, 10);' in _js_text:
                                        _js_text = _js_text.replace('}, 10);', '}, 25);')
                                    
                                    # Fix 3: Keep SWAILA on actionbar - MQPS visibility handles collision
                                    # No need to move to title channel as subtitle doesn't work properly
                                    _js_bytes = _js_text.encode('utf-8')
                                with open(_dest, 'wb') as _dst:
                                    _dst.write(_js_bytes)
                        for _item in _b_script_items:
                            _rel = _item[len('B/scripts/'):]
                            if _rel:
                                _dest = _os.path.join(_pack_dir, _rel)
                                _os.makedirs(_os.path.dirname(_dest), exist_ok=True)
                                _js_bytes = _zip_ref.read(_item)
                                # Apply JS compatibility patches to any script
                                if _rel.endswith('.js'):
                                    _js_text = _js_bytes.decode('utf-8', errors='ignore')
                                    # Fix 1: Strip empty setActionBar calls (prevents wiping other addons' data)
                                    _js_text = __import__('re').sub(
                                        r'(?:[A-Za-z_$][\w$]*\.)+setActionBar\s*\(\s*(?:\'\'|"")\s*\)',
                                        '(0)',
                                        _js_text
                                    )
                                    # Detect if this script is an actionbar-heavy addon
                                    _uses_actionbar = 'setActionBar' in _js_text
                                    _is_mqps = 'mqps' in _js_text.lower() or 'more_hunger_bar' in _js_text
                                    _has_timer = any(x in _js_text for x in ['runInterval', 'setInterval', 'setTimeout', 'runTimeout'])
                                    
                                    # Fix 2: Stagger ANY timed actionbar script to reduce collisions
                                    if _uses_actionbar and _has_timer and '}, 10);' in _js_text:
                                        _js_text = _js_text.replace('}, 10);', '}, 25);')
                                    
                                    # Fix 3: Keep SWAILA on actionbar - MQPS visibility handles collision
                                    # No need to move to title channel as subtitle doesn't work properly
                                    _js_bytes = _js_text.encode('utf-8')
                                with open(_dest, 'wb') as _dst:
                                    _dst.write(_js_bytes)

                    try:
                        _manifest_json = self._get_manifest_data(_mcpack_file)
                        if _manifest_json is None:
                            raise ValueError("Failed to parse manifest.json")
                    except KeyError:
                        log_error(KeyError)
                        _messagebox.showerror("Error", f"manifest.json not found in {_os.path.basename(_mcpack_file)}")
                        continue
                    except Exception as _e:
                        log_error(_e)
                        _messagebox.showerror("Error", f"Error reading manifest.json in {_os.path.basename(_mcpack_file)}: {str(_e)}")
                        continue

                    _entries = [_m.get("entry") for _m in _manifest_json.get("modules", []) if "entry" in _m]

                    for _entry in _entries:
                        if not _entry:
                            continue
                        try:
                            # Strip the leading 'scripts/' prefix from the entry path so we
                            # can locate the file inside the pack's isolated subdirectory.
                            _entry_rel      = _entry[len('scripts/'):] if _entry.startswith('scripts/') else _entry
                            _entry_basename = _os.path.basename(_entry_rel)
                            _new_name       = f"{_pack_num}_{_entry_basename}"

                            _old_path = _os.path.join(_pack_dir, _entry_rel)
                            _new_path = _os.path.join(_os.path.dirname(_old_path), _new_name)

                            # Fallback: entry declared without a subdir (e.g. "main.js")
                            if not _os.path.exists(_old_path):
                                _flat = _os.path.join(_pack_dir, _entry_basename)
                                if _os.path.exists(_flat):
                                    _old_path = _flat
                                    _new_path = _os.path.join(_pack_dir, _new_name)

                            if _os.path.exists(_old_path):
                                _os.rename(_old_path, _new_path)
                                _renamed_in_pack[_entry_basename] = _new_name
                                _imported_files.append(_new_path)
                            else:
                                _imported_files.append(_old_path)

                        except Exception as _e:
                            log_error(_e)
                            _messagebox.showerror("Error", f"Error processing entry {_entry} in {_os.path.basename(_mcpack_file)}: {str(_e)}")
                            continue

            except Exception as _e:
                log_error(_e)
                _messagebox.showerror("Error", f"Failed to process {_os.path.basename(_mcpack_file)}: {str(_e)}")

            _pack_info[_mcpack_file] = (_renamed_in_pack, _pack_dir)

        # ── Fix JS import paths before rename rewriting ──────────────────────
        # Two classes of import break when scripts move into an isolated subdir:
        #
        # 1. Bare module imports (import 'name' / import 'name.js') that relied on
        #    Bedrock resolving from the scripts/ root.  After isolation the file is
        #    in scripts/{uuid}/name.js but 'name' still resolves from scripts/ root
        #    which no longer has it.  Convert to './name' when the target file
        #    exists alongside the importing file.
        #
        # 2. Relative imports whose ../ count exceeds the file's nesting depth
        #    within the pack subdir.  Bedrock clamps resolution at the scripts/
        #    root, so 'scripts/a/b/c/file.js' with '../../../../x' resolves to
        #    'scripts/x'.  After isolation, the same file is at
        #    'scripts/{uuid}/a/b/c/file.js' (depth 4) and the same ../../../../
        #    resolves to 'scripts/x' — but the file is now 'scripts/{uuid}/x'.
        #    Cap excessive ../ to the file's actual depth within the pack dir so
        #    the import resolves to the correct location inside {uuid}/.
        for _mcpack_file, (_renamed_in_pack, _pack_dir) in _pack_info.items():
            if not _os.path.isdir(_pack_dir):
                continue
            _pack_dir_p = _pathlib.Path(_pack_dir)
            for _js_root, _, _js_files in _os.walk(_pack_dir):
                for _js_fname in _js_files:
                    if not _js_fname.endswith('.js'):
                        continue
                    _jfp = _os.path.join(_js_root, _js_fname)
                    try:
                        _jfp_p   = _pathlib.Path(_jfp)
                        _jfp_rel = _jfp_p.relative_to(_pack_dir_p)
                        _depth   = len(_jfp_rel.parent.parts)  # dirs deep from pack_dir
                        _jdir    = _jfp_p.parent

                        with open(_jfp, 'r', encoding='latin-1') as _jf:
                            _jcontent = _jf.read()
                        _joriginal = _jcontent

                        # ── 1. bare imports → ./relative ──────────────────────
                        def _fix_bare(m):
                            _pfx   = m.group(1)   # 'import' or 'from'
                            _q     = m.group(2)   # quote char
                            _spec  = m.group(3)   # the specifier
                            # Skip if already relative or a Bedrock built-in
                            if _spec.startswith(('.', '/', '@')) or not _spec:
                                return m.group(0)
                            # Try with and without .js extension
                            _bare_name = _spec if _spec.endswith('.js') else _spec + '.js'
                            _candidate = _jdir / _bare_name
                            if _candidate.exists():
                                return f'{_pfx} {_q}./{_spec}{_q}'
                            _candidate2 = _jdir / _spec
                            if _candidate2.exists():
                                return f'{_pfx} {_q}./{_spec}{_q}'
                            return m.group(0)

                        _jcontent = _re.sub(
                            r'\b(import|from)\s+(["\'])([^"\'./\n@][^"\'?\n]*)(\2)',
                            _fix_bare, _jcontent)

                        # ── 2. cap excessive ../ in relative imports ──────────
                        def _cap_dots(m):
                            _pfx  = m.group(1)   # 'import' or 'from'
                            _q    = m.group(2)   # quote char
                            _dots = m.group(3)   # the repeated ../ prefix
                            _rest = m.group(4)   # remainder of the path
                            _n    = _dots.count('../')
                            if _n <= _depth:
                                return m.group(0)
                            _capped = '../' * _depth
                            return f'{_pfx} {_q}{_capped}{_rest}{_q}'

                        _jcontent = _re.sub(
                            r'\b(import|from)\s+(["\'])((?:\.\./){2,})([^"\'?\n]+)(\2)',
                            _cap_dots, _jcontent)

                        # ── 3. self-rescheduling form delay fix ───────────────
                        # Addons like BetterCombat show a persistent ActionFormData that
                        # re-queues itself every N ticks via system.runTimeout inside a
                        # finally block.  When N is tiny (e.g. 20 ticks = 1 second) the
                        # form re-appears immediately after dismissal, covering the HUD
                        # and preventing title-based UI addons (e.g. Water Temperature
                        # System) from ever displaying their overlays.
                        # Raise the INITIAL declaration value to 600 ticks (30 s) while
                        # leaving any in-function reassignments (e.g. nextShowDelay = 0
                        # on button press) untouched so the toggle button still works.
                        if ('nextShowDelay' in _jcontent
                                and '.show(' in _jcontent
                                and 'runTimeout' in _jcontent):
                            def _fix_show_delay(m):
                                _val = int(m.group(1))
                                if _val < 100:
                                    return f'let nextShowDelay = 600'
                                return m.group(0)
                            _jcontent = _re.sub(
                                r'\blet\s+nextShowDelay\s*=\s*(\d+)',
                                _fix_show_delay, _jcontent)

                        # ── 4. setTitle() UI-binding prefix → add stayDuration ─
                        # The Water Temperature System (and similar addons) send titles
                        # whose text starts with special §-code sequences that the RP's
                        # hud_screen.json patches intercept and hide, replacing them with
                        # custom HUD elements (thermometer, thirst bar).  Without an
                        # explicit stayDuration the default ~3.5 s title window expires
                        # between thirst-floor-change events, making the custom HUD
                        # disappear.  Append TitleDisplayOptions to bare setTitle()
                        # calls whose argument string begins with multiple §-codes
                        # (\\u00A7 escape or latin-1 0xA7 byte) so they stay 10 s.
                        if '.setTitle(' in _jcontent:
                            # Match: .setTitle(TEMP_KEYS[level]);
                            _jcontent = _re.sub(
                                r'(\.setTitle\(TEMP_KEYS\[level\])\)',
                                r'\1, {fadeInDuration:0,stayDuration:200,fadeOutDuration:0})',
                                _jcontent)
                            # Match single-line: .setTitle("§§§§§§§§..." + expr);
                            _jcontent = _re.sub(
                                r'(\.setTitle\("(?:\\u00A7[a-zA-Z0-9]){3,}[^"]*"[^;{]*?)\)',
                                r'\1, {fadeInDuration:0,stayDuration:200,fadeOutDuration:0})',
                                _jcontent)
                            # Match multi-line thirst setTitle block (no existing 2nd arg)
                            # Pattern: .setTitle(\r?\n  "§§§..."  + expr\r?\n  );
                            # Use lambda to preserve original CRLF/LF style;
                            # [^;\r\n]* excludes \r so it is not swallowed into group 2
                            _nl = '\r\n' if '\r\n' in _jcontent else '\n'
                            def _fix_ml_title(m):
                                return (m.group(1) + _nl
                                        + m.group(2) + ','
                                        + _nl + m.group(3)
                                        + '{fadeInDuration:0,stayDuration:200,fadeOutDuration:0}'
                                        + _nl + m.group(3) + ');')
                            _jcontent = _re.sub(
                                r'(\.setTitle\()\s*\r?\n(\s*"(?:\\u00A7[a-zA-Z0-9]){3,}[^"\r\n]*"[^;\r\n]*)\r?\n(\s*)\);',
                                _fix_ml_title,
                                _jcontent)

                        # ── 5. :icon: shortcode → JS Unicode escape ───────────
                        # Some addons embed :heart: or :craftable_toggle_on:
                        # as literal ASCII placeholders, expecting them to
                        # render as Minecraft UI icons.  Replace with JS
                        # \uXXXX escapes so they render in Minecraft's font.
                        _SHORTCODE_MAP = {
                            ':heart:':               r'\u2764',  # ❤
                            ':heart_outline:':       r'\u2661',  # ♡
                            ':craftable_toggle_on:': r'\u2611',  # ☑
                            ':craftable_toggle_off:':r'\u2610',  # ☐
                            ':star:':                r'\u2605',  # ★
                            ':star_empty:':          r'\u2606',  # ☆
                        }
                        for _sc, _esc in _SHORTCODE_MAP.items():
                            if _sc in _jcontent:
                                _jcontent = _jcontent.replace(_sc, _esc)

                        # ── 6. entityHurt damagingEntity null-safety ──────────
                        # damagingEntity can be undefined for environmental
                        # damage (fall, fire, void). Using attacker.getComponent()
                        # without a null guard throws TypeError every time.
                        # Replace with optional chaining so the callback silently
                        # returns undefined instead of crashing.
                        if 'damagingEntity' in _jcontent and '.getComponent(' in _jcontent:
                            # Covers both renamed patterns: attacker.getComponent, source.getComponent
                            _jcontent = _re.sub(
                                r'\b(attacker|damagingEntity)\b\.getComponent\(',
                                r'\1?.getComponent(',
                                _jcontent)
                            _jcontent = _re.sub(
                                r'\b(attacker|damagingEntity)\b\.getComponent\(([^)]+)\)\.getEquipment\(',
                                r'\1?.getComponent(\2)?.getEquipment(',
                                _jcontent)

                        # ── 7. playerInteractWithBlock data.source → data.player ─
                        # Bedrock's PlayerInteractWithBlockBeforeEvent exposes
                        # .player, not .source.  Older packs use data.source which
                        # is undefined in current engine versions → TypeError.
                        # Replace with a safe fallback that works on both old and
                        # new API versions.
                        if 'playerInteractWithBlock' in _jcontent and 'data.source' in _jcontent:
                            _jcontent = _jcontent.replace(
                                'data.source.name',
                                '(data.source??data.player)?.name')
                            _jcontent = _jcontent.replace(
                                'data.source.dimension',
                                '(data.source??data.player)?.dimension')
                            # Guard the canonical assignment used by older packs:
                            #   const player = data.source;
                            # Use a tightly-scoped regex anchored to declaration
                            # keywords so comparison operators (===, !==) are
                            # never accidentally matched.
                            _jcontent = _re.sub(
                                r'\b(const|let|var)\s+(\w+)\s*=\s*data\.source\s*;',
                                r'\1 \2 = (data.source??data.player);',
                                _jcontent)

                        if _jcontent != _joriginal:
                            with open(_jfp, 'w', encoding='latin-1') as _jf:
                                _jf.write(_jcontent)
                    except Exception:
                        pass

        # Update import references and apply namespacing within each pack's isolated
        # directory only — prevents cross-pack import rewrites from corrupting unrelated scripts.
        for _mcpack_file, (_renamed_in_pack, _pack_dir) in _pack_info.items():
            if not _renamed_in_pack or not _os.path.isdir(_pack_dir):
                continue

            for _root, _, _files in _os.walk(_pack_dir):
                for _file in _files:
                    if not _file.endswith('.js'):
                        continue
                    try:
                        _file_path = _os.path.join(_root, _file)
                        with open(_file_path, 'r', encoding='latin-1') as _js_file:
                            _content = _js_file.read()

                        for _old_name, _new_name in _renamed_in_pack.items():
                            _old_wo_ext = _old_name.rsplit('.', 1)[0]
                            _new_wo_ext = _new_name.rsplit('.', 1)[0]
                            _pat_ext    = rf"(?<=['\"/]){_re.escape(_old_name)}(?=['\";])"
                            _pat_no_ext = rf"(?<=['\"/]){_re.escape(_old_wo_ext)}(?=['\";])"
                            _content = _re.sub(_pat_ext,    _new_name,    _content)
                            _content = _re.sub(_pat_no_ext, _new_wo_ext,  _content)

                        with open(_file_path, 'w', encoding='latin-1') as _js_file:
                            _js_file.write(_content)
                    except Exception as _e:
                        log_error(_e)
                        _messagebox.showerror("Error", f"Error updating import statements in {_file}: {str(_e)}")
                        continue

            # Namespace dynamic property keys and scoreboard objective names per pack
            # so scripts that shared a pack UUID before merging don't collide in the
            # combined pack's single UUID namespace.
            try:
                self._namespace_script_properties(_pack_dir, _mcpack_file, _renamed_in_pack)
            except Exception:
                pass

        _valid_imports = [f for f in _imported_files if _os.path.exists(f)]
        _logging.info(f"[_process_files] {len(_valid_imports)} entry files found across all packs -> writing CodeNex.js")
        for _dbg in _valid_imports:
            _logging.info(f"  import: {_os.path.relpath(_dbg, _scripts_path).replace(chr(92), '/')}")

        # Write imports to CodeNex.js only if the files exist.
        # Static imports MUST be used here — Bedrock resolves all static imports
        # synchronously before the first game tick runs. Dynamic imports (await import())
        # are async and cause top-level event subscriptions (world.afterEvents.playerSpawn
        # etc.) to miss the first tick, breaking spawn-item and UI addons like Lorewarden.
        with open(_main_js_path, 'w', encoding='utf-8') as _main_js_file:
            _main_js_file.write('// AutoBE merged script bridge — generated by CodeNex\n')
            _main_js_file.write('// Each pack script is imported once; dynamic property keys and\n')
            _main_js_file.write('// scoreboard objective names are auto-namespaced to prevent collisions.\n\n')
            _main_js_file.write(f'// {len(_imported_files)} pack(s) with scripts detected\n')
            _main_js_file.write('console.warn("[AutoBE CodeNex] Script bridge loading...");\n\n')
            for _imported_file in _imported_files:
                if _os.path.exists(_imported_file):
                    try:
                        _file_name = _os.path.relpath(_imported_file, _scripts_path).replace("\\", "/")
                        _main_js_file.write(f'import "./{_file_name}";\n')
                    except Exception as _e:
                        log_error(_e)
                        _messagebox.showerror("Error", f"Error writing to CodeNex.js for {_imported_file}: {str(_e)}")
                        continue

        # Append a startup-complete marker so the content log confirms all imports ran.
        try:
            with open(_main_js_path, 'a', encoding='utf-8') as _main_js_file:
                _main_js_file.write(f'\nconsole.warn("[AutoBE CodeNex] All {len(_imported_files)} pack script(s) loaded.");\n')
        except Exception:
            pass

        # Strip any stale bare-name imports that were never renamed (legacy safety net).
        try:
            with open(_main_js_path, 'r') as _main_js_file:
                _main_js_content = _main_js_file.read()

            _main_js_content = _main_js_content.replace('import "./main.js";', '')
            _main_js_content = _main_js_content.replace('import "./Main.js";', '')

            with open(_main_js_path, 'w', encoding='utf-8') as _main_js_file:
                _main_js_file.write(_main_js_content)
        except Exception as _e:
            log_error(_e)
            _messagebox.showerror("Error", f"Error finalizing CodeNex.js: {str(_e)}")
    
    # ──────────────────────────────────────────────────────────────────────────

    # (Player Body Shapes feature removed)
    _PLACEHOLDER_PBS = None  # kept for settings compatibility; feature is disabled
    def _scan_script_runtime_conflicts(self, selected_files):
        """
        Scan every JS script in every selected pack for direct runtime entity/world
        property writes.  Returns a dict:
            {(component_or_obj, property_name): [(pack_display_name, file_path, line_no), ...]}
        Only entries with 2+ packs are genuine conflicts.  Runs fast (regex only, no AST).
        """
        # Patterns that indicate a direct runtime property write — covers the most common cases
        _WRITE_PATTERNS = [
            # entity.getComponent("minecraft:health").currentValue = ...
            (_re.compile(r'getComponent\s*\(\s*["\']([^"\']+)["\']\s*\)\s*\.\s*(\w+)\s*=(?!=)', _re.IGNORECASE), 1, 2),
            # entity.nameTag = ...  / entity.isSneaking = ...  / entity.selectedSlot = ...
            (_re.compile(r'\bentity\s*\.\s*(nameTag|selectedSlot|isSneaking|isFlying|isClimbing|isGliding)\s*=(?!=)', _re.IGNORECASE), None, 1),
            # player.nameTag = ...  etc.
            (_re.compile(r'\bplayer\s*\.\s*(nameTag|selectedSlot|isSneaking|isFlying)\s*=(?!=)', _re.IGNORECASE), None, 1),
            # world.setDynamicProperty (bare, no colon) — already namespaced, but catch remaining bare ones
            # entity.applyKnockback / teleport / kill — can conflict if both call them
            (_re.compile(r'\bentity\s*\.\s*(applyKnockback|teleport|kill|triggerEvent)\s*\(', _re.IGNORECASE), None, 1),
        ]

        # {(comp_or_obj, prop): [(pack_name, file_path, line_no), ...]}
        results = {}

        for pack_path in selected_files:
            pack_display = _os.path.basename(pack_path)
            pack_display = _re.sub(r'\.(mcpack|mcaddon)$', '', pack_display, flags=_re.IGNORECASE)
            pack_display = _re.sub(r'_modified$', '', pack_display, flags=_re.IGNORECASE)

            try:
                with _zipfile.ZipFile(pack_path, 'r') as zf:
                    js_items = [n for n in zf.namelist() if n.endswith('.js')]
                    for js_item in js_items:
                        try:
                            raw = zf.read(js_item).decode('latin-1')
                        except Exception:
                            continue
                        for lineno, line in enumerate(raw.splitlines(), 1):
                            for pattern, comp_group, prop_group in _WRITE_PATTERNS:
                                for m in pattern.finditer(line):
                                    comp = m.group(comp_group) if comp_group else 'entity'
                                    prop = m.group(prop_group)
                                    key = (comp, prop)
                                    bucket = results.setdefault(key, [])
                                    # Only add this pack once per (comp, prop)
                                    if not any(p == pack_display for p, _, _ in bucket):
                                        bucket.append((pack_display, js_item, lineno))
            except Exception:
                continue

        # Keep only entries where 2+ different packs hit the same (comp, prop)
        return {k: v for k, v in results.items() if len(v) >= 2}

    @staticmethod
    def _make_pack_ns(pack_path):
        """Derive a short stable namespace token from a pack filename."""
        name = _os.path.basename(pack_path)
        name = _re.sub(r'\.(mcpack|mcaddon)$', '', name, flags=_re.IGNORECASE)
        name = _re.sub(r'_modified$', '', name, flags=_re.IGNORECASE)
        name = _re.sub(r'_\d+$', '', name)
        ns = _re.sub(r'[^a-z0-9]', '', name.lower())[:8]
        return ns or 'pack'

    def _namespace_script_properties(self, scripts_path, pack_path, renamed_files_in_pack):
        """
        After merging, all scripts share one behavior-pack UUID, so dynamic property
        keys and scoreboard objective names that were previously isolated per-pack UUID
        now collide.  This pass prefixes every bare key with a short pack token so each
        pack's data stays isolated while remaining internally self-consistent.

        Transforms (per-pack, consistent):
          setDynamicProperty("score", v)  →  setDynamicProperty("ns:score", v)
          getDynamicProperty("score")     →  getDynamicProperty("ns:score")
          addObjective("kills", ...)      →  addObjective("ns_kills", ...)
          getObjective("kills")           →  getObjective("ns_kills")
        Keys/names that already contain ':' or look pre-namespaced are left alone.
        """
        ns = self._make_pack_ns(pack_path)

        for root, _, files in _os.walk(scripts_path):
            for fname in files:
                if not fname.endswith('.js'):
                    continue
                fpath = _os.path.join(root, fname)
                try:
                    with open(fpath, 'r', encoding='latin-1') as f:
                        content = f.read()
                    original = content

                    # --- Dynamic properties: prefix bare keys (no colon) ---
                    def _prefix_dynprop(m):
                        key = m.group(2)
                        if ':' in key:
                            return m.group(0)
                        return m.group(1) + ns + ':' + key + m.group(3)

                    content = _re.sub(
                        r'((?:set|get)DynamicProperty\s*\(\s*["\'])([^"\':\n]+)(["\'])',
                        _prefix_dynprop, content)

                    # --- Scoreboard objectives: prefix names (max 16 chars total) ---
                    short_ns = ns[:4]  # 4 chars + '_' + 11 chars = 16

                    def _prefix_obj(m):
                        method = m.group(1)
                        q = m.group(2)
                        name = m.group(3)
                        # Skip if already looks prefixed (contains _)
                        if '_' in name and name.index('_') <= 5:
                            return m.group(0)
                        new_name = (short_ns + '_' + name)[:16]
                        return method + q + new_name + q

                    content = _re.sub(
                        r'((?:add|get|remove)Objective\s*\(\s*)(["\'])([^"\']{1,16})\2',
                        _prefix_obj, content)

                    if content != original:
                        with open(fpath, 'w', encoding='latin-1') as f:
                            f.write(content)
                except Exception:
                    pass

    def _extract_feature_rules(self, _pack_zip, _item, _folder_name, _output_zip):
        with _pack_zip.open(_item) as _file_data:
            _output_zip.writestr(_os.path.join(_folder_name, _os.path.basename(_item.filename)), _file_data.read())
    
    def _merge_entity_json_simple(self, _json_list, _file_name):
        """Simple union merge for entity JSON files to preserve all custom features."""
        if not _json_list:
            return {}
        if len(_json_list) == 1:
            return _json_list[0]
        
        merged = _json.deepcopy(_json_list[0])
        
        for json_obj in _json_list[1:]:
            merged = self._deep_merge_union(merged, json_obj)
        
        return merged
    
    def _deep_merge_union(self, base, overlay):
        """Deep merge with union strategy - overlay adds to base, never overwrites."""
        if not isinstance(base, dict) or not isinstance(overlay, dict):
            return overlay
        
        for key, value in overlay.items():
            if key not in base:
                # Key doesn't exist in base, add it
                base[key] = value
            elif isinstance(base[key], dict) and isinstance(value, dict):
                # Both are dicts, merge recursively
                base[key] = self._deep_merge_union(base[key], value)
            elif isinstance(base[key], list) and isinstance(value, list):
                # Both are lists, concatenate with duplicate removal
                for item in value:
                    if item not in base[key]:
                        base[key].append(item)
            # For primitives, keep base (first wins)
        
        return base
    
    def _merge_json(self, _json_list, _file_name):
        # Use simple union merge for entity files to preserve all custom features
        if _file_name.endswith('.entity.json') or 'entity' in _file_name.lower():
            return self._merge_entity_json_simple(_json_list, _file_name)
        
        def normalize_string(s):
            try:
                s = _re.sub(r'\\s*=\\s*', '=', s)
                s = s.replace("1st_person", "first_person").replace("3rd_person", "third_person")
                s = s.replace("v.is_first_person", "variable.is_first_person").replace("q.is_spectator", "query.is_spectator")
                return s
            except Exception as e:
                print(f"Error normalizing string '{s}': {e}")
                return s

        def remove_duplicates_from_list(_list, check_keys=False):
            unique_list = []
            seen = set()
            for item in _list:
                try:
                    if isinstance(item, str):
                        normalized_item = normalize_string(item)
                        if normalized_item not in seen:
                            unique_list.append(item)
                            seen.add(normalized_item)
                    elif isinstance(item, dict):
                        normalized_dict = {normalize_string(k): normalize_string(v) if isinstance(v, str) else v for k, v in item.items()}
                        item_tuple = tuple(sorted(normalized_dict.keys())) if check_keys else tuple(sorted(normalized_dict.items()))
                        if item_tuple not in seen:
                            unique_list.append(item)
                            seen.add(item_tuple)
                except Exception as e:
                    print(f"Error processing item '{item}': {e}")
            return unique_list

        def merge_dicts(merged_dict, new_dict):
            for k, v in new_dict.items():
                try:
                    norm_key = normalize_string(k)
                    if norm_key in merged_dict:
                        if isinstance(merged_dict[norm_key], dict) and isinstance(v, dict):
                            merged_dict[norm_key] = self._merge_json([merged_dict[norm_key], v], _file_name)
                        elif isinstance(merged_dict[norm_key], list) and isinstance(v, list):
                            check_keys = _file_name == "player.json" and norm_key in ['render_controllers', 'animations', 'animate', 'particle_effects']
                            merged_dict[norm_key] = remove_duplicates_from_list(merged_dict[norm_key] + v, check_keys)
                        else:
                            if normalize_string(str(v)) != normalize_string(str(merged_dict[norm_key])):
                                print(f"Duplicate detected and removed: {_file_name}: {k}")
                    else:
                        merged_dict[norm_key] = v
                except Exception as e:
                    print(f"Error processing key '{k}' with value '{v}': {e}")
            return merged_dict

        _merged = {}
        _format_version_set = False
        _format_version = None
        _warning_shown = False  # Flag to track if the warning has been shown

        # Dictionary to track MCPACK format versions
        mcpack_versions = {}
        differing_mcpack_names = set()  # Track MCPACK names with different format versions

        # Use the MCPACK names from _add_files
        mcpack_names = getattr(self, 'mcpack_names', [])

        # Process each JSON object
        for index, _json in enumerate(_json_list):
            try:
                if 'format_version' in _json:
                    current_version = _json['format_version']
                    # Track format_version for each MCPACK
                    mcpack_name = mcpack_names[index] if index < len(mcpack_names) else 'Unknown MCPACK'
                    if mcpack_name in mcpack_versions:
                        if mcpack_versions[mcpack_name] != current_version:
                            differing_mcpack_names.add(mcpack_name)
                    mcpack_versions[mcpack_name] = current_version
                    
                    if not _format_version_set:
                        _format_version = current_version
                        _format_version_set = True
                    elif current_version != _format_version:
                        # Update the set of differing MCPACK names
                        differing_mcpack_names.add(mcpack_name)

                for _key, _value in _json.items():
                    if _key == "format_version" and not _format_version_set:
                        _merged[_key] = _value
                        _format_version_set = True
                    elif _file_name in ("player.animation_controllers.json", "player.render_controllers.json", "player.animation.json"):
                        # For animation/render controller files use first-wins per named entry.
                        # Deep-merging two incompatible animation state machines produces broken results
                        # (e.g. sideways first-person camera). Keep the first pack's definition for any
                        # controller/animation name that already exists; add unique names from later packs.
                        if _key not in _merged:
                            _merged[_key] = _value
                        elif isinstance(_merged[_key], dict) and isinstance(_value, dict):
                            for _sub_k, _sub_v in _value.items():
                                if _sub_k not in _merged[_key]:  # first-wins per named entry
                                    _merged[_key][_sub_k] = _sub_v
                        elif isinstance(_merged[_key], list) and isinstance(_value, list):
                            _merged[_key] = remove_duplicates_from_list(_merged[_key] + _value)
                    elif _file_name == "_ui_defs.json":
                        if _key not in _merged:
                            _merged[_key] = _value
                        else:
                            if isinstance(_value, list):
                                if not isinstance(_merged[_key], list):
                                    _merged[_key] = [_merged[_key]]
                                _merged[_key].extend(_value)
                                _merged[_key] = remove_duplicates_from_list(_merged[_key])
                            elif isinstance(_value, str):
                                if isinstance(_merged[_key], list):
                                    normalized_value = normalize_string(_value)
                                    existing_values = [normalize_string(i) for i in _merged[_key]]
                                    if normalized_value not in existing_values:
                                        _merged[_key].append(_value)
                                else:
                                    _merged[_key] = [_merged[_key], _value]
                            else:
                                _merged[_key] = _value
                    elif _file_name == "player.json":
                        if _key not in _merged:
                            _merged[_key] = _value
                        else:
                            if isinstance(_value, list):
                                check_keys = _key in ['render_controllers', 'animations', 'animate', 'particle_effects']
                                merged_list = _merged[_key] + _value
                                _merged[_key] = remove_duplicates_from_list(merged_list, check_keys)
                            elif isinstance(_merged[_key], dict) and isinstance(_value, dict):
                                _merged[_key] = self._merge_json([_merged[_key], _value], _file_name)
                            else:
                                _merged[_key] = _value
                    elif _file_name in ("item_texture.json", "terrain_texture.json"):
                        if _key not in _merged:
                            _merged[_key] = _value
                        elif _key == "texture_data" and isinstance(_merged[_key], dict) and isinstance(_value, dict):
                            # First-wins: only add texture entries not already present so earlier packs' textures are preserved
                            for _tk, _tv in _value.items():
                                if _tk not in _merged[_key]:
                                    _merged[_key][_tk] = _tv
                        elif isinstance(_merged[_key], dict) and isinstance(_value, dict):
                            _merged[_key] = self._merge_json([_merged[_key], _value], _file_name)
                        elif isinstance(_merged[_key], list) and isinstance(_value, list):
                            _merged[_key] = remove_duplicates_from_list(_merged[_key] + _value)
                    elif _file_name == "crafting_item_catalog.json":
                        # Merge crafting/creative catalog: union groups by category_name
                        if _key not in _merged:
                            _merged[_key] = _value
                        elif _key == "minecraft:crafting_items_catalog" and isinstance(_merged[_key], dict) and isinstance(_value, dict):
                            merged_cat = _merged[_key]
                            new_cat = _value
                            if "categories" in new_cat:
                                if "categories" not in merged_cat:
                                    merged_cat["categories"] = []
                                # Index existing categories by category_name
                                _existing = {c.get("category_name"): c for c in merged_cat["categories"] if isinstance(c, dict)}
                                for _nc in new_cat["categories"]:
                                    if not isinstance(_nc, dict): continue
                                    _cname = _nc.get("category_name")
                                    if _cname in _existing:
                                        # Union the groups lists — append new groups not already present by icon
                                        _eg = _existing[_cname].setdefault("groups", [])
                                        _existing_icons = {g.get("group_identifier", {}).get("icon") for g in _eg if isinstance(g, dict)}
                                        for _ng in _nc.get("groups", []):
                                            if isinstance(_ng, dict):
                                                _icon = _ng.get("group_identifier", {}).get("icon")
                                                if _icon not in _existing_icons:
                                                    _eg.append(_ng)
                                                    _existing_icons.add(_icon)
                                    else:
                                        merged_cat["categories"].append(_nc)
                                        _existing[_cname] = _nc
                        elif isinstance(_merged[_key], dict) and isinstance(_value, dict):
                            _merged[_key] = self._merge_json([_merged[_key], _value], _file_name)
                    elif _file_name == "sound_definitions.json":
                        if _key not in _merged:
                            _merged[_key] = _value
                        elif _key == "sound_definitions" and isinstance(_merged[_key], dict) and isinstance(_value, dict):
                            # First-wins: preserve existing sound entries; add new ones from later packs
                            for _sk, _sv in _value.items():
                                if _sk not in _merged[_key]:
                                    _merged[_key][_sk] = _sv
                                elif isinstance(_merged[_key][_sk], dict) and isinstance(_sv, dict):
                                    # Union the sounds arrays so both packs' sound files are included
                                    existing_sounds = _merged[_key][_sk].get("sounds", [])
                                    new_sounds = _sv.get("sounds", [])
                                    if isinstance(existing_sounds, list) and isinstance(new_sounds, list):
                                        combined = existing_sounds + [s for s in new_sounds if s not in existing_sounds]
                                        _merged[_key][_sk]["sounds"] = combined
                        elif isinstance(_merged[_key], dict) and isinstance(_value, dict):
                            _merged[_key] = self._merge_json([_merged[_key], _value], _file_name)
                    elif _file_name == "hud_screen.json":
                        # Special handling for hud_screen.json to preserve modifications arrays
                        if _key not in _merged:
                            _merged[_key] = _value
                        elif isinstance(_merged[_key], dict) and isinstance(_value, dict):
                            # Recursively merge dictionaries, but concatenate modifications arrays
                            if _key == "modifications" and isinstance(_merged[_key], list) and isinstance(_value, list):
                                # Concatenate modifications arrays to preserve all UI injection operations
                                _merged[_key] = _merged[_key] + _value
                            else:
                                _merged[_key] = self._merge_json([_merged[_key], _value], _file_name)
                        elif isinstance(_merged[_key], list) and isinstance(_value, list):
                            # Concatenate lists for hud_screen.json
                            _merged[_key] = _merged[_key] + _value
                        else:
                            _merged[_key] = _value
                    else:
                        # Enhanced merging for entity files and other common conflict files
                        if _key not in _merged:
                            _merged[_key] = _value
                        else:
                            # Special handling for entity file properties that should be merged
                            if _file_name.endswith('.json') and _key in ['components', 'component_groups', 'events', 'spawn_rules', 'behaviors']:
                                # These properties should be merged, not overwritten
                                if isinstance(_merged[_key], dict) and isinstance(_value, dict):
                                    # Merge components/component_groups/events dictionaries
                                    _merged[_key] = self._merge_json([_merged[_key], _value], _file_name)
                                elif isinstance(_merged[_key], list) and isinstance(_value, list):
                                    # Merge spawn_rules/behaviors lists
                                    merged_list = _merged[_key] + _value
                                    _merged[_key] = remove_duplicates_from_list(merged_list, check_keys=True)
                                else:
                                    # Fallback: try to merge if types match
                                    if type(_merged[_key]) == type(_value):
                                        if isinstance(_value, dict):
                                            _merged[_key] = self._merge_json([_merged[_key], _value], _file_name)
                                        elif isinstance(_value, list):
                                            merged_list = _merged[_key] + _value
                                            _merged[_key] = remove_duplicates_from_list(merged_list, check_keys=True)
                                        else:
                                            _merged[_key] = _value
                                    else:
                                        _merged[_key] = _value
                            elif isinstance(_merged[_key], list) and isinstance(_value, list):
                                # Merge lists by combining and removing duplicates
                                merged_list = _merged[_key] + _value
                                _merged[_key] = remove_duplicates_from_list(merged_list, check_keys=True)
                            elif isinstance(_merged[_key], dict) and isinstance(_value, dict):
                                # Recursively merge dictionaries
                                _merged[_key] = self._merge_json([_merged[_key], _value], _file_name)
                            else:
                                # For primitive values, keep the last one (but log if different)
                                if str(_merged[_key]) != str(_value) and _key not in ['format_version', 'description']:
                                    # UI visibility conditions must be combined, not overwritten.
                                    # If Pack A says "(not 'mqps')" and Pack B says "(not '!')",
                                    # the merged pack should hide text matching EITHER prefix.
                                    if (_key == 'visible'
                                            and 'hud_screen' in _file_name
                                            and isinstance(_merged[_key], str)
                                            and isinstance(_value, str)):
                                        _merged[_key] = f'({_merged[_key]}) && ({_value})'
                                    else:
                                        _merged[_key] = _value
            except Exception as e:
                print(f"Error processing JSON data for file '{_file_name}': {e}")

        # blocks.json post-processing: strip legacy geometry/shape specs from
        # custom-namespace block entries so they don't clash with minecraft:geometry
        # components defined in the block's own JSON, which produces in-game warnings.
        if _file_name == "blocks.json":
            _LEGACY_SHAPE_KEYS = {"geometry", "carried_textures", "isotropic", "brightness_gamma"}
            for _bk in list(_merged.keys()):
                if ':' in _bk and not _bk.startswith('minecraft:') and isinstance(_merged[_bk], dict):
                    for _lk in _LEGACY_SHAPE_KEYS:
                        _merged[_bk].pop(_lk, None)

        # Client entity post-processing: strip empty-string keys from geometry/textures/materials
        # to prevent Molang errors like "geometry. not found in entity friendly name list"
        if _file_name.endswith('.entity.json') or _file_name.endswith('.entity.json'.replace('entity.', 'client_entity.')):
            for _root_key in ('minecraft:client_entity', 'minecraft:entity'):
                _desc = _merged.get(_root_key, {}).get('description', {})
                for _sect in ('geometry', 'textures', 'materials', 'animations'):
                    if _sect in _desc and isinstance(_desc[_sect], dict):
                        _desc[_sect] = {k: v for k, v in _desc[_sect].items() if v not in ('', None)}

        return _merged
    
    def _merge_player_json(self, _player_json_list, file_path=None):
        """Merge player JSON files using universal merger for intelligent conflict resolution."""
        merger = UniversalJsonMerger()
        return merger.merge_json_list(_player_json_list, file_path=file_path)

    def _merge_dicts(self, _dict1, _dict2):
        for _key, _value in _dict2.items():
            if _key in _dict1:
                if isinstance(_dict1[_key], dict) and isinstance(_value, dict):
                    _dict1[_key] = self._merge_dicts(_dict1[_key], _value)
                elif isinstance(_dict1[_key], list) and isinstance(_value, list):
                    _dict1[_key].extend(_value)
                else:
                    _dict1[_key] = _value
            else:
                _dict1[_key] = _value
        return _dict1

    def _merge_lang_files(self, _lang_list):
        _merged_lang = {}   # key -> value (first-wins)
        _comment_lines = [] # preserve ## comment/section lines from first pack only
        _seen_comments = set()
        for _idx, _lang_data in enumerate(_lang_list):
            for _line in _lang_data.splitlines():
                _stripped = _line.strip()
                if not _stripped:
                    continue
                if _stripped.startswith('##'):
                    # Only keep comment lines from the first pack to avoid duplicated section headers
                    if _idx == 0 and _stripped not in _seen_comments:
                        _comment_lines.append((_stripped, len(_merged_lang)))
                        _seen_comments.add(_stripped)
                    continue
                if '=' in _stripped:
                    _key, _value = _stripped.split('=', 1)
                    _key = _key.strip()
                    if _key and _key not in _merged_lang:  # first-wins
                        _merged_lang[_key] = _value
        # Build output: interleave comment lines at their original positions
        _kv_pairs = [f"{k}={v}" for k, v in _merged_lang.items()]
        _output_lines = []
        _comment_idx = 0
        for _i, _pair in enumerate(_kv_pairs):
            while _comment_idx < len(_comment_lines) and _comment_lines[_comment_idx][1] <= _i:
                _output_lines.append(_comment_lines[_comment_idx][0])
                _comment_idx += 1
            _output_lines.append(_pair)
        # Append any trailing comment lines
        while _comment_idx < len(_comment_lines):
            _output_lines.append(_comment_lines[_comment_idx][0])
            _comment_idx += 1
        return '\n'.join(_output_lines)

    def _load_json_with_comments(self, _file):
        """Load JSON file with robust comment and error handling. Uses same logic as _get_manifest_data."""
        try:
            # Read the file content - try UTF-8 first, fallback to latin-1
            try:
                _file_content = _file.read().decode('utf-8')
            except UnicodeDecodeError:
                _file_content = _file.read().decode('latin-1', errors='ignore')
            
            # Try json5 first (handles comments natively)
            json5_available = True
            try:
                import json5 as _json5
            except ImportError:
                json5_available = False
                _logging.warning("json5 library not installed, attempting manual comment removal.")
            
            if json5_available:
                try:
                    return _json5.loads(_file_content)
                except Exception as json5_error:
                    # json5 failed, try with cleaned content
                    _logging.warning(f"json5 parsing failed for {_file.name}, attempting cleanup: {json5_error}")
                    # Fall through to manual comment removal
            
            # Fallback: try to remove comments manually
            # Remove block comments /* ... */ (non-greedy)
            _file_content_clean = _re.sub(r'/\*.*?\*/', '', _file_content, flags=_re.DOTALL)
            
            # Remove line comments // ... (but not in strings)
            lines = _file_content_clean.split('\n')
            cleaned_lines = []
            for line in lines:
                # Find // that's not inside a string
                in_string = False
                escape_next = False
                new_line = []
                i = 0
                while i < len(line):
                    char = line[i]
                    if escape_next:
                        new_line.append(char)
                        escape_next = False
                    elif char == '\\' and in_string:
                        new_line.append(char)
                        escape_next = True
                    elif char == '"' and not escape_next:
                        in_string = not in_string
                        new_line.append(char)
                    elif char == '/' and i + 1 < len(line) and line[i+1] == '/' and not in_string:
                        # Found // comment outside string
                        break
                    else:
                        new_line.append(char)
                    i += 1
                cleaned_lines.append(''.join(new_line))
            _file_content_clean = '\n'.join(cleaned_lines)
            
            # Remove trailing commas before closing braces/brackets
            _file_content_clean = _re.sub(r',\s*([}\]])', r'\1', _file_content_clean)
            
            # Try parsing with standard json
            try:
                return _json.loads(_file_content_clean)
            except Exception as json_error:
                _logging.warning(f"Error parsing JSON (after cleanup) in file: {_file.name}: {json_error}")
                _logging.info(f"Attempting JSON extraction for {_file.name}...")
                # Last resort: try to extract just the JSON structure
                try:
                    # Find first { and matching closing }
                    start_idx = _file_content_clean.find('{')
                    if start_idx >= 0:
                        # Count braces to find the matching closing brace
                        brace_count = 0
                        in_string = False
                        escape_next = False
                        i = start_idx
                        while i < len(_file_content_clean):
                            char = _file_content_clean[i]
                            if escape_next:
                                escape_next = False
                            elif char == '\\' and in_string:
                                escape_next = True
                            elif char == '"' and not escape_next:
                                in_string = not in_string
                            elif not in_string:
                                if char == '{':
                                    brace_count += 1
                                elif char == '}':
                                    brace_count -= 1
                                    if brace_count == 0:
                                        # Found matching closing brace
                                        json_str = _file_content_clean[start_idx:i+1]
                                        return _json.loads(json_str)
                            i += 1
                except Exception as extract_error:
                    _logging.error(f"Failed to extract JSON from {_file.name}: {extract_error}")
            
            return None
        except Exception as e:
            _logging.error(f"Error reading or parsing JSON file: {_file.name}: {e}")
            return None

    def _get_manifest_data(self, _file):
        """Extract and parse manifest.json from a pack file. Handles JSON with comments using json5."""
        try:
            with _zipfile.ZipFile(_file, 'r') as _pack_zip:
                # Try to find manifest.json (case-insensitive, may be in root or subdirectory)
                # Prefer root level, then behavior_pack (for .mcaddon script-version grouping), then any subdirectory
                manifest_path = None
                root_manifest = None
                behavior_pack_manifest = None
                first_subdir_manifest = None
                for name in _pack_zip.namelist():
                    name_lower = name.lower()
                    if name_lower == 'manifest.json':
                        root_manifest = name
                        break
                    if name_lower.endswith('/manifest.json'):
                        if first_subdir_manifest is None:
                            first_subdir_manifest = name
                        if 'behavior_pack' in name_lower:
                            behavior_pack_manifest = name
                
                if root_manifest:
                    manifest_path = root_manifest
                elif behavior_pack_manifest:
                    manifest_path = behavior_pack_manifest
                elif first_subdir_manifest:
                    manifest_path = first_subdir_manifest

                # ── Nested .mcpack fallback (common .mcaddon layout) ─────────
                # .mcaddon files usually contain .mcpack zip entries rather than
                # raw files, so manifest.json lives inside those inner archives.
                if not manifest_path:
                    import io as _io
                    _inner_candidates = [
                        n for n in _pack_zip.namelist()
                        if n.lower().endswith(('.mcpack', '.zip')) and '/' not in n
                    ]
                    # Prefer a BP entry, then any entry
                    _inner_candidates.sort(
                        key=lambda x: (0 if any(k in x.lower() for k in ('behavior', '_bp', 'bp_')) else 1)
                    )
                    for _inner_name in _inner_candidates:
                        try:
                            with _pack_zip.open(_inner_name) as _inner_data:
                                _inner_bytes = _inner_data.read()
                            with _zipfile.ZipFile(_io.BytesIO(_inner_bytes), 'r') as _inner_zip:
                                for _iname in _inner_zip.namelist():
                                    if _iname.lower() == 'manifest.json':
                                        with _inner_zip.open(_iname) as _imf:
                                            _raw = _imf.read()
                                        try:
                                            _mc = _raw.decode('utf-8')
                                        except UnicodeDecodeError:
                                            _mc = _raw.decode('latin-1', errors='ignore')
                                        try:
                                            import json5 as _json5
                                            return _json5.loads(_mc)
                                        except Exception:
                                            pass
                                        try:
                                            return _json.loads(_mc)
                                        except Exception:
                                            pass
                                        break
                        except Exception:
                            continue

                if manifest_path:
                    with _pack_zip.open(manifest_path) as _manifest_file:
                        try:
                            # Read the manifest file content - try UTF-8 first, fallback to latin-1
                            try:
                                _manifest_content = _manifest_file.read().decode('utf-8')
                            except UnicodeDecodeError:
                                _manifest_content = _manifest_file.read().decode('latin-1', errors='ignore')
                            
                            # Use json5 library which natively supports comments
                            # No need to manually remove comments - json5 handles them
                            # Try json5 first (handles comments natively)
                            json5_available = True
                            try:
                                import json5 as _json5
                            except ImportError:
                                json5_available = False
                                _logging.warning("json5 library not installed, attempting manual comment removal.")
                            
                            if json5_available:
                                try:
                                    _manifest_data = _json5.loads(_manifest_content)
                                    return _manifest_data
                                except Exception as json5_error:
                                    # json5 failed, try with cleaned content
                                    _logging.warning(f"json5 parsing failed for {_file}, attempting cleanup: {json5_error}")
                                    # Fall through to manual comment removal
                            
                            # Fallback: try to remove comments manually
                            # Remove block comments /* ... */ (non-greedy)
                            _manifest_content_clean = _re.sub(r'/\*.*?\*/', '', _manifest_content, flags=_re.DOTALL)
                            
                            # Remove line comments // ... (but not in strings)
                            lines = _manifest_content_clean.split('\n')
                            cleaned_lines = []
                            for line in lines:
                                # Find // that's not inside a string
                                in_string = False
                                escape_next = False
                                new_line = []
                                i = 0
                                while i < len(line):
                                    char = line[i]
                                    if escape_next:
                                        new_line.append(char)
                                        escape_next = False
                                    elif char == '\\' and in_string:
                                        new_line.append(char)
                                        escape_next = True
                                    elif char == '"' and not escape_next:
                                        in_string = not in_string
                                        new_line.append(char)
                                    elif char == '/' and i + 1 < len(line) and line[i+1] == '/' and not in_string:
                                        # Found // comment outside string
                                        break
                                    else:
                                        new_line.append(char)
                                    i += 1
                                cleaned_lines.append(''.join(new_line))
                            _manifest_content_clean = '\n'.join(cleaned_lines)
                            
                            # Remove trailing commas before closing braces/brackets
                            _manifest_content_clean = _re.sub(r',\s*([}\]])', r'\1', _manifest_content_clean)
                            
                            # Try parsing with standard json
                            try:
                                _manifest_data = _json.loads(_manifest_content_clean)
                                return _manifest_data
                            except Exception as json_error:
                                _logging.warning(f"Error parsing manifest.json (after cleanup) in file: {_file}: {json_error}")
                                _logging.info(f"Attempting JSON extraction for {_file}...")
                                # Last resort: try to extract just the JSON structure
                                try:
                                    # Find first { and matching closing }
                                    start_idx = _manifest_content_clean.find('{')
                                    if start_idx >= 0:
                                        # Count braces to find the matching closing brace
                                        brace_count = 0
                                        end_idx = start_idx
                                        in_string = False
                                        escape_next = False
                                        
                                        for i in range(start_idx, len(_manifest_content_clean)):
                                            char = _manifest_content_clean[i]
                                            if escape_next:
                                                escape_next = False
                                            elif char == '\\' and in_string:
                                                escape_next = True
                                            elif char == '"' and not escape_next:
                                                in_string = not in_string
                                            elif not in_string:
                                                if char == '{':
                                                    brace_count += 1
                                                elif char == '}':
                                                    brace_count -= 1
                                                    if brace_count == 0:
                                                        end_idx = i
                                                        break
                                        
                                        if end_idx > start_idx and brace_count == 0:
                                            extracted_json = _manifest_content_clean[start_idx:end_idx+1]
                                            _manifest_data = _json.loads(extracted_json)
                                            _logging.info(f"Successfully extracted and parsed JSON for {_file}")
                                            return _manifest_data
                                        else:
                                            _logging.error(f"Could not find matching braces for {_file} (start: {start_idx}, end: {end_idx}, brace_count: {brace_count})")
                                except Exception as extract_error:
                                    _logging.error(f"JSON extraction failed for {_file}: {extract_error}")
                                return None
                        except Exception as e:
                            _logging.error(f"Error reading manifest.json in file: {_file}: {e}")
                            return None
                else:
                    _logging.warning(f"manifest.json not found in file: {_file}")
                    return None
        except _zipfile.BadZipFile:
            _logging.error(f"Invalid ZIP file: {_file}")
            return None
        except Exception as e:
            _logging.error(f"Error opening file: {_file}: {e}")
            return None
        
        return None

    def _create_manifest(self):
        # Persist BP/RP header UUIDs for this output directory so they remain stable
        # across re-merges.  Bedrock stores the UUID in world_behavior_packs.json;
        # if the UUID changes every merge the world keeps running the old (stale) pack.
        _uuid_cache_path = _os.path.join(self._out_dir, ".autobe_uuids.json")
        _uuid_cache = {}
        try:
            if _os.path.isfile(_uuid_cache_path):
                with open(_uuid_cache_path, 'r', encoding='utf-8') as _uf:
                    _uuid_cache = _json.load(_uf)
        except Exception:
            _uuid_cache = {}

        def _stable_uuid(key):
            if key not in _uuid_cache or not _uuid_cache[key]:
                _uuid_cache[key] = str(_uuid.uuid4())
            return _uuid_cache[key]

        _bp_header_uuid = _stable_uuid("bp_header")
        _rp_header_uuid = _stable_uuid("rp_header")
        _bp_module_uuid = _stable_uuid("bp_module")
        _rp_module_uuid = _stable_uuid("rp_module")

        try:
            with open(_uuid_cache_path, 'w', encoding='utf-8') as _uf:
                _json.dump(_uuid_cache, _uf, indent=2)
        except Exception:
            pass

        # Retrieve highest versions found during extraction
        highest_bp_version = getattr(self, 'highest_bp_version', None)
        highest_rp_version = getattr(self, 'highest_rp_version', None)
        highest_server_version_full = getattr(self, 'highest_server_version_full', "1.13.0")
        highest_server_ui_version_full = getattr(self, 'highest_server_ui_version_full', "1.2.0")
        highest_gametest_version_full = getattr(self, 'highest_gametest_version_full', None)

        # Minimum required version for Minecraft Bedrock (1.13.0 is the minimum)
        min_required_version = [1, 13, 0]
        # Default fallback version (only used if no versions were found at all)
        default_version = [1, 21, 30]

        def compare_versions(version_a, version_b):
            """Compares two versions (assumed to be lists of integers). Returns True if version_a >= version_b"""
            if version_a is None:
                return False
            if version_b is None:
                return True
            for i in range(3):
                if version_a[i] > version_b[i]:
                    return True
                elif version_a[i] < version_b[i]:
                    return False
            return True  # Equal versions

        # Use the highest found version, ensuring it's at least the minimum required
        if highest_bp_version is None:
            # No version found, use default
            highest_bp_version = default_version
        elif not compare_versions(highest_bp_version, min_required_version):
            # Version found but below minimum, use minimum
            highest_bp_version = min_required_version

        if highest_rp_version is None:
            # No version found, use default
            highest_rp_version = default_version
        elif not compare_versions(highest_rp_version, min_required_version):
            # Version found but below minimum, use minimum
            highest_rp_version = min_required_version

        # Behavior Pack Manifest
        _manifest_behavior = {
            "format_version": 2,
            "header": {
                "description": "Modpack Created Using AutoBE - CodeNex",
                "name": "AutoBE Behavior",
                "uuid": _bp_header_uuid,
                "version": [1, 0, 0],
                "min_engine_version": highest_bp_version
            },
            "modules": [
                {
                    "description": "Created Using AutoBE - CodeNex",
                    "type": "data",
                    "uuid": _bp_module_uuid,
                    "version": [1, 0, 0]
                },
                {
                    "description": "gametesting",
                    "language": "javascript",
                    "type": "script",
                    "uuid": str(_uuid.uuid4()),
                    "version": [1, 0, 0],
                    "entry": "scripts/CodeNex.js"
                }
            ],
            "capabilities": ["script_eval"],
            "dependencies": [
                {
                    "uuid": _rp_header_uuid,
                    "version": [1, 0, 0]
                },
                {
                    "module_name": "@minecraft/server",
                    "version": highest_server_version_full
                },
                {
                    "module_name": "@minecraft/server-ui",
                    "version": highest_server_ui_version_full
                }
            ],
            "metadata": {
                "authors": ["CodeNex"]
            }
        }

        # Add @minecraft/server-gametest dependency if a version was found
        if highest_gametest_version_full:
            _manifest_behavior["dependencies"].append({
                "module_name": "@minecraft/server-gametest",
                "version": highest_gametest_version_full
            })

        # Resource Pack Manifest
        _manifest_resource = {
            "format_version": 2,
            "header": {
                "description": "Modpack Created Using AutoBE - CodeNex",
                "name": "AutoBE Resource",
                "uuid": _rp_header_uuid,
                "version": [1, 0, 0],
                "min_engine_version": highest_rp_version
            },
            "modules": [
                {
                    "description": "Created Using AutoBE - CodeNex",
                    "type": "resources",
                    "uuid": _rp_module_uuid,
                    "version": [1, 0, 0]
                }
            ],
            "dependencies": [
                {
                    "uuid": _bp_header_uuid,
                    "version": [1, 0, 0]
                }
            ],
            "metadata": {
                "authors": ["CodeNex"]
            }
        }

        # Paths for the pack files
        _bp_path = _os.path.join(self._out_dir, "behavior_pack.zip")
        _rp_path = _os.path.join(self._out_dir, "resource_pack.zip")

        # Find the first available pack_icon from source packs to use for both output packs
        _icon_bytes = None
        try:
            for _src in getattr(self, '_files', []):
                if _icon_bytes:
                    break
                try:
                    with _zipfile.ZipFile(_src, 'r') as _sz:
                        for _n in _sz.namelist():
                            _nb = _n.lower().split('/')[-1]
                            if _nb in ('pack_icon.png', 'pack_icon.jpg', 'pack_icon.jpeg'):
                                _icon_bytes = _sz.read(_n)
                                break
                except Exception:
                    pass
        except Exception:
            pass

        try:
            # Write behavior pack manifest to zip
            with _zipfile.ZipFile(_bp_path, 'a') as _bp_zip:
                _bp_zip.writestr("manifest.json", _json.dumps(_manifest_behavior, indent=2))
                if _icon_bytes:
                    _bp_zip.writestr("pack_icon.png", _icon_bytes)

            # Write resource pack manifest to zip
            with _zipfile.ZipFile(_rp_path, 'a') as _rp_zip:
                _rp_zip.writestr("manifest.json", _json.dumps(_manifest_resource, indent=2))
                if _icon_bytes:
                    _rp_zip.writestr("pack_icon.png", _icon_bytes)

            # Convert zip files to .mcpack files
            _bp_new_path = _os.path.join(self._out_dir, "behavior_pack.mcpack")
            _shutil.move(_bp_path, _bp_new_path)

            _rp_new_path = _os.path.join(self._out_dir, "resource_pack.mcpack")
            _shutil.move(_rp_path, _rp_new_path)

        except Exception as e:
            log_error(e)
            _messagebox.showerror("Error", f"An error occurred during manifest creation: {str(e)}")

    def _move_tick_and_delete_functions(self):
        _functions_folder = _os.path.join(self._out_dir, "functions")
        _entities_folder = _os.path.join(self._out_dir, "entities")
        
        _bp_path = _os.path.join(self._out_dir, "behavior_pack.mcpack")
        _rp_path = _os.path.join(self._out_dir, "resource_pack.mcpack")

        _bp_functions_folder = "functions"
        _rp_functions_folder = f"{_bp_functions_folder}/"
        
        _bp_entities_folder = "entities"
        _rp_entities_folder = f"{_bp_entities_folder}/"

        _bp_tick_path = f"{_bp_functions_folder}/tick.json"
        _rp_tick_path = f"{_rp_functions_folder}tick.json"
        
        _bp_player_path = f"{_bp_entities_folder}/player.json"
        _rp_player_path = f"{_rp_entities_folder}player.json"

        try:
            # Move tick.json from resource pack to behavior pack
            with _zipfile.ZipFile(_rp_path, 'r') as _rp_zip:
                with _zipfile.ZipFile(_bp_path, 'a') as _bp_zip:
                    try:
                        _tick_data = _rp_zip.read(_rp_tick_path)
                        _bp_zip.writestr(_bp_tick_path, _tick_data)
                    except KeyError:
                        _logging.debug(f"'{_rp_tick_path}' not found in resource pack.")
                    
                    try:
                        _player_data = _rp_zip.read(_rp_player_path)
                        _bp_zip.writestr(_bp_player_path, _player_data)
                    except KeyError:
                        _logging.debug(f"'{_rp_player_path}' not found in resource pack.")

        except Exception as _e:
            _logging.error(f"An error occurred during the initial file operations: {_e}")

        try:
            # Extract and delete functions folder
            with _zipfile.ZipFile(_rp_path, 'a') as _rp_zip:
                for _file in list(_rp_zip.namelist()):
                    if _file.startswith(_rp_functions_folder):
                        try:
                            _rp_zip.extract(_file, self._out_dir)
                            _os.remove(_os.path.join(self._out_dir, _file))
                        except FileNotFoundError:
                            _logging.warning(f"File '{_file}' not found during extraction.")
                try:
                    _shutil.rmtree(_functions_folder)
                except FileNotFoundError:
                    _logging.debug(f"Folder '{_functions_folder}' not found during removal.")

        except Exception as _e:
            _logging.error(f"An error occurred while processing functions folder: {_e}")

        try:
            # Extract and delete entities folder
            with _zipfile.ZipFile(_rp_path, 'a') as _rp_zip:
                for _file in list(_rp_zip.namelist()):
                    if _file.startswith(_rp_entities_folder):
                        try:
                            _rp_zip.extract(_file, self._out_dir)
                            _os.remove(_os.path.join(self._out_dir, _file))
                        except FileNotFoundError:
                            _logging.warning(f"File '{_file}' not found during extraction.")
                try:
                    _shutil.rmtree(_entities_folder)
                except FileNotFoundError:
                    _logging.debug(f"Folder '{_entities_folder}' not found during removal.")

        except Exception as _e:
            _messagebox.showinfo("Error", f"An error occurred: {_e}")

    def _delete_manifest_files(self):
        _packs = ["behavior_pack.zip", "resource_pack.zip"]

        for _pack in _packs:
            _pack_path = _os.path.join(self._out_dir, _pack)
            _temp_pack_path = _os.path.join(self._out_dir, f"temp_{_pack}")

            try:
                with _zipfile.ZipFile(_pack_path, 'r') as _zip_read:
                    with _zipfile.ZipFile(_temp_pack_path, 'w') as _zip_write:
                        for _item in _zip_read.infolist():
                            if _item.filename not in ["manifest.json", "package.json", "contents.json", ".data", "package-lock.json", "signatures.json"]:
                                _data = _zip_read.read(_item.filename)
                                _zip_write.writestr(_item, _data)

                _os.remove(_pack_path)
                _os.rename(_temp_pack_path, _pack_path)

            except _zipfile.BadZipFile:
                _logging.error(f"Bad ZIP file: {_pack_path}", exc_info=True)
                _messagebox.showerror("Error", f"Bad ZIP file: {_pack_path}")
            except FileNotFoundError:
                _logging.warning(f"File not found: {_pack_path}")
            except Exception as _e:
                pass

    def _move_and_cleanup(self):
        _bp_path = _os.path.join(self._out_dir, "Behavior_packs", "scripts", "scripts")
        _mainjs_path = _os.path.join(self._out_dir, "Behavior_packs", "scripts", "CodeNex.js")
        _scriptswe_path = _os.path.join(self._out_dir, "scripts")

        try:
            _dest_scripts = _os.path.join(self._out_dir, "scripts")
            if _os.path.isdir(_bp_path):
                if _os.path.isdir(_dest_scripts):
                    _shutil.rmtree(_dest_scripts)
                _shutil.move(_bp_path, self._out_dir)
        except FileNotFoundError:
            print(f"Directory '{_bp_path}' does not exist.")

        try:
            if _os.path.exists(_scriptswe_path) and not _os.path.isdir(_scriptswe_path):
                _os.remove(_scriptswe_path)  # remove stale file artefact before makedirs
            _os.makedirs(_scriptswe_path, exist_ok=True)
            _dest_js = _os.path.join(_scriptswe_path, _os.path.basename(_mainjs_path))
            if _os.path.exists(_mainjs_path):
                if _os.path.exists(_dest_js):
                    _os.remove(_dest_js)
                _shutil.move(_mainjs_path, _scriptswe_path)
        except FileNotFoundError:
            print(f"File '{_mainjs_path}' does not exist.")

        try:
            _bp_path = _os.path.join(self._out_dir, "Behavior_packs")
            _shutil.rmtree(_bp_path)
        except FileNotFoundError:
            print(f"Directory '{_bp_path}' does not exist.")

    def _update_behavior_pack(self):
        _bp_path = _os.path.join(self._out_dir, "behavior_pack.mcpack")
        _scripts_folder = _os.path.join(self._out_dir, "scripts")

        if _os.path.exists(_bp_path):
            _temp_dir = _tempfile.mkdtemp(prefix='temp_unpack_')
            _os.makedirs(_temp_dir, exist_ok=True)

            with _zipfile.ZipFile(_bp_path, 'r') as _zip_ref:
                _zip_ref.extractall(_temp_dir)

            _scripts_path_in_temp = _os.path.join(_temp_dir, "scripts")
            if (_os.path.exists(_scripts_path_in_temp)):
                _shutil.rmtree(_scripts_path_in_temp)
                
            _subpacks_path_in_temp = _os.path.join(_temp_dir, "subpacks")
            if (_os.path.exists(_subpacks_path_in_temp)):
                _shutil.rmtree(_subpacks_path_in_temp)

            if _os.path.isdir(_scripts_folder):
                _shutil.copytree(_scripts_folder, _scripts_path_in_temp)

            # Determine whether CodeNex.js contains real import statements.
            # If not (e.g. the "none" version group has no scripted packs),
            # strip the script module + script_eval capability + script API
            # dependencies from the manifest.  Bedrock refuses to load a BP
            # that declares @minecraft/server@1.13.0 (the fallback default)
            # because that version no longer exists in modern game builds.
            _codenex_path = _os.path.join(_scripts_path_in_temp, "CodeNex.js")
            _has_real_imports = False
            try:
                if _os.path.isfile(_codenex_path):
                    with open(_codenex_path, 'r', encoding='utf-8', errors='ignore') as _cj:
                        _has_real_imports = any(
                            line.strip().startswith('import ') for line in _cj
                        )
            except Exception:
                pass

            if not _has_real_imports:
                # Remove the now-useless scripts folder from the temp dir so
                # the empty CodeNex.js doesn't bloat the data-only output pack.
                try:
                    if _os.path.isdir(_scripts_path_in_temp):
                        _shutil.rmtree(_scripts_path_in_temp)
                except Exception:
                    pass
                # Patch the manifest to strip script-related entries.
                _manifest_tmp = _os.path.join(_temp_dir, "manifest.json")
                try:
                    with open(_manifest_tmp, 'r', encoding='utf-8') as _mf:
                        _mdata = _json.load(_mf)
                    # Remove script module entries
                    _mdata['modules'] = [
                        m for m in _mdata.get('modules', [])
                        if m.get('type') != 'script'
                    ]
                    # Remove script_eval capability
                    _caps = _mdata.get('capabilities', [])
                    if 'script_eval' in _caps:
                        _caps.remove('script_eval')
                    # Remove script API dependencies (@minecraft/server*, not uuid-based)
                    _script_mods = {'@minecraft/server', '@minecraft/server-ui',
                                    '@minecraft/server-gametest', '@minecraft/server-admin'}
                    _mdata['dependencies'] = [
                        d for d in _mdata.get('dependencies', [])
                        if d.get('module_name') not in _script_mods
                    ]
                    with open(_manifest_tmp, 'w', encoding='utf-8') as _mf:
                        _json.dump(_mdata, _mf, indent=2)
                    _logging.info("[_update_behavior_pack] No real imports — stripped script module from manifest.")
                except Exception as _me:
                    _logging.warning(f"[_update_behavior_pack] Could not patch manifest: {_me}")

            _new_bp_path = _os.path.join(self._out_dir, "behavior_pack.mcpack")
            with _zipfile.ZipFile(_new_bp_path, 'w') as _zip_ref:
                for _root, _dirs, _files in _os.walk(_temp_dir):
                    for _file in _files:
                        _file_path = _os.path.join(_root, _file)
                        _arcname = _os.path.relpath(_file_path, _temp_dir)
                        _zip_ref.write(_file_path, _arcname)

            _shutil.rmtree(_temp_dir)
            if _os.path.isdir(_scripts_folder):
                _shutil.rmtree(_scripts_folder)
            elif _os.path.exists(_scripts_folder):
                _os.remove(_scripts_folder)  # stale file artefact — remove it
            _logging.info("Process 3/4 Completed Successfully!")
        else:
            _logging.error("behavior_pack.mcpack not found", exc_info=True)
            _messagebox.showwarning("Error", "behavior_pack.mcpack not found")

    def _merge_flipbook_textures(self, _selected_files):
        if not _selected_files:
            _logging.error("No .mcpack files selected", exc_info=True)
            _messagebox.showerror(_("msg.error"), _("process.select_mcpacks_only"))
            return

        _merged_textures = []

        for _mcpack_file in _selected_files:
            try:
                with _zipfile.ZipFile(_mcpack_file, 'r') as _zip_ref:
                    try:
                        _texture_data = _zip_ref.read('textures/flipbook_textures.json').decode('latin-1')
                        _texture_data_lines = _texture_data.splitlines()
                        _filtered_texture_data = '\n'.join([_line for _line in _texture_data_lines if not _line.strip().startswith('//')])
                        try:
                            _textures_json = _json.loads(_filtered_texture_data)
                        except Exception:
                            continue
                        if isinstance(_textures_json, list):
                            _merged_textures.extend(_textures_json)
                    except KeyError:
                        pass
            except Exception as _e:
                _logging.error(f"An error occurred while merging flipbook textures: {_e}", exc_info=True)

        _merged_zip_path = _os.path.join(self._out_dir, "flipbook_textures.zip")
        with _zipfile.ZipFile(_merged_zip_path, 'w') as _merged_zip:
            _merged_zip.writestr('flipbook_textures.json', _json.dumps(_merged_textures))

    def _merge_textures_list(self, _selected_files):
        if not _selected_files:
            _logging.error("No .mcpack files selected", exc_info=True)
            _messagebox.showerror(_("msg.error"), _("process.select_mcpacks_only"))
            return

        _merged_textures = []

        for _mcpack_file in _selected_files:
            try:
                with _zipfile.ZipFile(_mcpack_file, 'r') as _zip_ref:
                    try:
                        _texture_data = _zip_ref.read('textures/textures_list.json').decode('latin-1')
                        _texture_data_lines = _texture_data.splitlines()
                        _filtered_texture_data = '\n'.join([_line for _line in _texture_data_lines if not _line.strip().startswith('//')])
                        try:
                            _textures_json = _json.loads(_filtered_texture_data)
                        except Exception:
                            continue
                        if isinstance(_textures_json, list):
                            _merged_textures.extend(_textures_json)
                    except KeyError:
                        pass
            except Exception as _e:
                _logging.error(f"An error occurred while merging textures list: {_e}", exc_info=True)

        _merged_zip_path = _os.path.join(self._out_dir, "textures_list.zip")
        with _zipfile.ZipFile(_merged_zip_path, 'w') as _merged_zip:
            _merged_zip.writestr('textures_list.json', _json.dumps(_merged_textures))

    def _extract_and_delete_zip_files(self):
        _flipbook_zip_path = _os.path.join(self._out_dir, "flipbook_textures.zip")
        _textures_zip_path = _os.path.join(self._out_dir, "textures_list.zip")

        try:
            with _zipfile.ZipFile(_flipbook_zip_path, 'r') as _flipbook_zip:
                _flipbook_zip.extract('flipbook_textures.json', self._out_dir)
        except FileNotFoundError:
            pass

        try:
            with _zipfile.ZipFile(_textures_zip_path, 'r') as _textures_zip:
                _textures_zip.extract('textures_list.json', self._out_dir)
        except FileNotFoundError:
            pass

        try:
            _os.remove(_flipbook_zip_path)
        except FileNotFoundError:
            pass

        try:
            _os.remove(_textures_zip_path)
        except FileNotFoundError:
            pass

    def _move_to_resource_pack(self):
        _rp_path = _os.path.join(self._out_dir, "resource_pack.mcpack")
        _textures_folder_name = "textures"

        if not _os.path.exists(_rp_path):
            _logging.warning("resource_pack.mcpack not found in output directory", exc_info=True)
            _messagebox.showwarning("Warning", "resource_pack.mcpack not found in output directory")
            return

        try:
            _temp_dir = _tempfile.mkdtemp(prefix='temp_unpack_resource_pack_')
            _os.makedirs(_temp_dir, exist_ok=True)
                
            with _zipfile.ZipFile(_rp_path, 'r') as _zip_ref:
                _zip_ref.extractall(_temp_dir)

            _functions_path_in_temp = _os.path.join(_temp_dir, "functions")
            if (_os.path.exists(_functions_path_in_temp)):
                _shutil.rmtree(_functions_path_in_temp)
                
            _entities_path_in_temp = _os.path.join(_temp_dir, "entities")
            if (_os.path.exists(_entities_path_in_temp)):
                _shutil.rmtree(_entities_path_in_temp)
                
            _subpacks_path_in_temp = _os.path.join(_temp_dir, "subpacks")
            if (_os.path.exists(_subpacks_path_in_temp)):
                _shutil.rmtree(_subpacks_path_in_temp)

            _textures_folder = _os.path.join(_temp_dir, _textures_folder_name)

            _flipbook_textures_source = _os.path.join(self._out_dir, "flipbook_textures.json")
            _flipbook_textures_dest = _os.path.join(_textures_folder, "flipbook_textures.json")
            _shutil.move(_flipbook_textures_source, _flipbook_textures_dest)

            _textures_list_source = _os.path.join(self._out_dir, "textures_list.json")
            _textures_list_dest = _os.path.join(_textures_folder, "textures_list.json")
            _shutil.move(_textures_list_source, _textures_list_dest)

            _new_rp_path = _os.path.join(self._out_dir, "updated_resource_pack.mcpack")
            with _zipfile.ZipFile(_new_rp_path, 'w') as _zip_ref:
                for _root, _dirs, _files in _os.walk(_temp_dir):
                    for _file in _files:
                        _file_path = _os.path.join(_root, _file)
                        _arcname = _os.path.relpath(_file_path, _temp_dir)
                        _zip_ref.write(_file_path, _arcname)

            _shutil.rmtree(_temp_dir)
            _shutil.move(_new_rp_path, _rp_path)
            _shutil.rmtree(_flipbook_textures_source)
            _shutil.rmtree(_textures_list_source)
            _logging.info("Process 4/4 Completed Successfully!")

        except Exception as _e:
            pass
            
    def _show_help(self):
        _help_window = _tk.Toplevel(self._root)
        self._apply_window_icon(_help_window)
        _help_window.title("Help")
        _help_window.geometry("800x800")
        _help_window.configure(bg='#0A0A0A')

        _help_text = """
        How To Use AutoBE
        
        Test Addons Individually:
        Test each addon individually in Minecraft before merging to check compatibility and functionality.
        
        Add Files:
        Click 'Add Files' to select .mcpack files you want to merge.
        Use Ctrl (or Cmd on Mac) to select multiple files.
        
        Check Packs:
        Click 'Check Packs' to see which Minecraft version each addon belongs to.
        Organize addons by version into separate folders (e.g., 1.16, 1.21, etc.).
        
        Merge by Version:
        Only merge addons from the same version (e.g., merge all 1.16 addons together).
        Do not merge addons from different versions (e.g., 1.16 with 1.21).
        
        Handling Single Addons:
        If an addon is the only one for its version, or if it breaks merged packs, handle it alone. 
        Add it without merging to resolve conflicts.
        
        Start Process:
        Click 'Browse' to select the output directory.
        Click 'Start Process' to merge selected packs.
        
        Testing and Troubleshooting:
        Test merged packs in Minecraft.
        If issues occur, remove problematic addons and add them separately.
        Re-merge compatible addons as needed.
        
        Important Notes:
        Always test addons before and after merging.
        Ensure you have rights to use or distribute the addons.
        
        CodeNex is not responsible for misuse of this tool.
        Property of CodeNex
        """

        _help_label = _tk.Label(_help_window, text=_help_text, bg='#0A0A0A', fg='#E1E1E1', font=("Helvetica", 12))
        _help_label.pack(padx=10, pady=10)

    def mcpacker_process_files(self, input_files, output_dir):
        import shutil
        failed, success, tempdirs = [], [], []
        total_files = len(input_files)
        
        # Get the selected mode
        mode = getattr(self, 'mcpacker_mode_var', _tk.StringVar(value="pack")).get()
        
        # Step 1: Reading Files
        self._root.after(0, lambda: self._update_mcpacker_progress(1, 10, f"Reading {total_files} file(s)..."))
        
        if mode == "extract":
            # Extraction mode: Extract .mcpack/.mcaddon files to folders
            self._root.after(0, lambda: self._update_mcpacker_progress(2, 25, "Preparing extraction..."))
            
            for idx, in_file in enumerate(input_files):
                try:
                    progress = 25 + int((idx / total_files) * 70)
                    file_name = _os.path.basename(in_file)
                    self._root.after(0, lambda p=progress, f=file_name: self._update_mcpacker_progress(2, p, f"Extracting: {f}..."))
                    
                    # Check if file is .mcpack or .mcaddon
                    if not in_file.lower().endswith(('.mcpack', '.mcaddon', '.zip')):
                        failed.append((in_file, "Not a .mcpack, .mcaddon, or .zip file"))
                        continue
                    
                    # Create output folder name
                    base_name = _os.path.splitext(_os.path.basename(in_file))[0]
                    out_folder = _os.path.join(output_dir, base_name)
                    
                    # If folder exists, add number suffix
                    counter = 1
                    original_out_folder = out_folder
                    while _os.path.exists(out_folder):
                        out_folder = f"{original_out_folder}_{counter}"
                        counter += 1
                    
                    # Extract the archive
                    with _zipfile.ZipFile(in_file, 'r') as zip_ref:
                        zip_ref.extractall(out_folder)
                    
                    success.append(out_folder)
                    
                except Exception as e:
                    failed.append((in_file, str(e)))
            
            # Step 4: Finalizing
            self._root.after(0, lambda: self._update_mcpacker_progress(4, 90, "Finalizing..."))
            
        else:
            # Pack mode: Original behavior - convert folders to .mcpack
            # Step 2: Finding Packs
            self._root.after(0, lambda: self._update_mcpacker_progress(2, 25, "Finding valid packs in files..."))
            all_packs = []
            for idx, in_file in enumerate(input_files):
                try:
                    progress = 25 + int((idx / total_files) * 30)
                    self._root.after(0, lambda p=progress, f=_os.path.basename(in_file): self._update_mcpacker_progress(2, p, f"Finding packs in: {f}..."))
                    packs = find_valid_packs(in_file)
                    if not packs:
                        failed.append((in_file, "No manifest.json found"))
                        continue
                    all_packs.append((in_file, packs))
                except Exception as e:
                    failed.append((in_file, str(e)))
            
            # Step 3: Packaging Files
            self._root.after(0, lambda: self._update_mcpacker_progress(3, 55, "Packaging files into MCPACK format..."))
            
            total_packs = sum(len(packs) for _, packs in all_packs)
            pack_count = 0
            for in_file, packs in all_packs:
                for pack_folder in packs:
                    try:
                        base_name = _os.path.splitext(_os.path.basename(in_file))[0]
                        out_name = base_name + ".mcpack"
                        if len(packs) > 1:
                            idx = packs.index(pack_folder) + 1
                            out_name = f"{base_name}_{idx}.mcpack"
                        out_path = _os.path.join(output_dir, out_name)
                        
                        progress = 55 + int((pack_count / total_packs) * 35) if total_packs > 0 else 55
                        self._root.after(0, lambda p=progress, n=out_name: self._update_mcpacker_progress(3, p, f"Packaging: {n}..."))
                        
                        zip_pack_folder(pack_folder, out_path)
                        success.append(out_path)
                        if pack_folder.startswith(_tempfile.gettempdir()):
                            tempdirs.append(pack_folder)
                        pack_count += 1
                    except Exception as e:
                        failed.append((in_file, str(e)))
            
            # Step 4: Finalizing
            self._root.after(0, lambda: self._update_mcpacker_progress(4, 90, "Finalizing and cleaning up..."))
        for d in tempdirs:
            try:
                shutil.rmtree(d)
            except:
                pass
        
        # Show completion message in progress display
        if failed:
            failed_list = "\n".join([f"- {_os.path.basename(fname)}: {reason}" for fname, reason in failed[:5]])
            if len(failed) > 5:
                failed_list += f"\n... and {len(failed) - 5} more"
            if mode == "extract":
                message = f"Completed: {len(success)} extracted, {len(failed)} failed"
                self._root.after(0, lambda: self._update_mcpacker_progress(4, 100, message))
                error_msg = f"Extracted {len(success)} folder(s).\n\nFailed files:\n{failed_list}"
                self._root.after(0, lambda: _messagebox.showerror(_("mcpacker.some_files_failed"), error_msg))
            else:
                message = f"Completed: {len(success)} exported, {len(failed)} failed"
                self._root.after(0, lambda: self._update_mcpacker_progress(4, 100, message))
                error_msg = f"Exported {len(success)} MCPACK(s).\n\nFailed files:\n{failed_list}"
                self._root.after(0, lambda: _messagebox.showerror(_("mcpacker.some_files_failed"), error_msg))
        else:
            if mode == "extract":
                message = f"Successfully extracted {len(success)} folder(s)! ✓"
                self._root.after(0, lambda: self._update_mcpacker_progress(4, 100, message))
            else:
                message = f"Successfully exported {len(success)} MCPACK(s)! ✓"
                self._root.after(0, lambda: self._update_mcpacker_progress(4, 100, message))

    def _update_mcpacker_progress(self, step, progress_percent, message):
        """Update the MCPACKER progress display with current step and message."""
        if hasattr(self, '_mcpacker_progress_step_label'):
            self._mcpacker_progress_step_label.config(text=message)
            self._mcpacker_progress['value'] = progress_percent
            self._root.update_idletasks()
            
            # Update step indicators
            if hasattr(self, '_mcpacker_step_labels') and 1 <= step <= 4:
                for i in range(4):
                    if i < step - 1:
                        # Completed steps
                        self._mcpacker_step_labels[i]['status'].config(text="✓", fg='#9333ea')
                        self._mcpacker_step_labels[i]['label'].config(fg='#FFFFFF')
                    elif i == step - 1:
                        # Current step
                        self._mcpacker_step_labels[i]['status'].config(text="→", fg='#9333ea')
                        self._mcpacker_step_labels[i]['label'].config(fg='#9333ea')
                    else:
                        # Pending steps
                        self._mcpacker_step_labels[i]['status'].config(text="○", fg='#666666')
                        self._mcpacker_step_labels[i]['label'].config(fg='#999999')
                # Mark all as complete if step 4 is done
                if step == 4:
                    for i in range(4):
                        self._mcpacker_step_labels[i]['status'].config(text="✓", fg='#9333ea')
                        self._mcpacker_step_labels[i]['label'].config(fg='#FFFFFF')

    def _set_mcpacker_mode(self, mode):
        """Set the MCPACKER processing mode."""
        _logging.debug(f"_set_mcpacker_mode called with mode: {mode}")
        self.mcpacker_mode_var.set(mode)
        self._update_mcpacker_mode_labels()
        # Settings will be saved automatically via trace_add
    
    
    def _update_mcpacker_mode_labels(self):
        """Update step labels based on selected mode."""
        if hasattr(self, '_mcpacker_step_labels') and len(self._mcpacker_step_labels) >= 4:
            mode = self.mcpacker_mode_var.get()
            if mode == "extract":
                self._mcpacker_step_labels[2]['label'].config(text=_("mcpacker.extracting"))
            else:
                self._mcpacker_step_labels[2]['label'].config(text=_("mcpacker.packaging"))
    
    def _reset_mcpacker_progress(self):
        """Reset MCPACKER progress display to initial state."""
        if hasattr(self, '_mcpacker_progress_step_label'):
            self._mcpacker_progress_step_label.config(text=_("app.ready_to_process"))
            self._mcpacker_progress['value'] = 0
            if hasattr(self, '_mcpacker_step_labels'):
                for step_info in self._mcpacker_step_labels:
                    step_info['status'].config(text="○", fg='#666666')
                    step_info['label'].config(fg='#999999')

    def start_mcpacker(self):
        files = self._mcpacker_files  # Use stored file paths
        output_dir = self.output_dir_var.get()
        if not files or not output_dir:
            _messagebox.showerror(_("msg.error"), _("process.select_files_and_output"))
            return
        
        # Disable start button during processing
        self._btn_mcpacker_start.config(state='disabled')
        
        # Run processing in a separate thread to prevent UI freezing
        def process_thread():
            try:
                self._root.after(0, lambda: self._reset_mcpacker_progress())
                self._root.after(0, lambda: self._update_mcpacker_progress(0, 0, "Initializing process..."))
                self.mcpacker_process_files(files, output_dir)
                self._root.after(0, lambda: self._update_mcpacker_progress(4, 100, "Processing completed successfully! ✓"))
                # Clear selected files and output so tab is ready for next run
                self._root.after(0, lambda: self._reset_mcpacker_list())
                
            except Exception as e:
                _logging.error("An error occurred during MCPACKER process", exc_info=True)
                self._root.after(0, lambda: _messagebox.showerror(_("msg.error"), _f("process.an_error_occurred", error=e)))
                self._root.after(0, lambda: self._update_mcpacker_progress(0, 0, f"Error: {str(e)}"))
            finally:
                # Re-enable start button
                self._root.after(0, lambda: self._btn_mcpacker_start.config(state='normal'))
        
        threading.Thread(target=process_thread, daemon=True).start()

def _run_splash_then_app():
    """Show opening.gif splash from locales for a minimum time, then start the main app. Works for all users (verified and unverified)."""
    _init_translations()
    # Don't call basicConfig here - logging is already configured with the proper file path at module level
    # Calling basicConfig without filename would default to current directory (Program Files when installed as exe)
    # which causes permission errors when not run as admin

    splash_root = _tk.Tk()
    splash_root.withdraw()
    splash_root.configure(bg='#000000')
    splash_root.overrideredirect(True)
    splash_root.attributes('-topmost', True)

    gif_path = None
    for name in ('opening.gif', 'open.gif'):
        p = _os.path.join(_LOCALE_DIR, name)
        if _os.path.isfile(p):
            gif_path = p
            break

    splash_frames = []
    frame_delay_ms = 50
    splash_w, splash_h = 400, 300
    MAX_SPLASH_W, MAX_SPLASH_H = 900, 700  # same max size as AutoBE window

    if gif_path and _PIL_AVAILABLE and _PIL_Image is not None and _PIL_ImageTk is not None:
        try:
            img = _PIL_Image.open(gif_path)
            w, h = img.size
            if w > MAX_SPLASH_W or h > MAX_SPLASH_H:
                r = min(MAX_SPLASH_W / w, MAX_SPLASH_H / h)
                splash_w, splash_h = int(w * r), int(h * r)
            else:
                splash_w, splash_h = w, h
            thumb_resample = getattr(_PIL_Image.Resampling, 'LANCZOS', None) or getattr(_PIL_Image, 'LANCZOS', 1)
            try:
                n = 0
                while True:
                    img.seek(n)
                    f = img.copy()
                    if f.mode in ('RGBA', 'LA', 'P'):
                        if f.mode == 'P' and 'transparency' in img.info:
                            f = f.convert('RGBA')
                        bg = _PIL_Image.new('RGB', f.size, (0, 0, 0))
                        if f.mode in ('RGBA', 'LA'):
                            bg.paste(f, mask=f.split()[-1])
                        else:
                            bg.paste(f)
                        f = bg
                    elif f.mode != 'RGB':
                        f = f.convert('RGB')
                    f.thumbnail((splash_w, splash_h), thumb_resample)
                    splash_frames.append(_PIL_ImageTk.PhotoImage(f))
                    n += 1
            except EOFError:
                pass
            if getattr(img, 'info', None) and 'duration' in img.info:
                frame_delay_ms = max(20, min(img.info['duration'], 200))
        except Exception:
            splash_frames = []

    if not splash_frames and gif_path:
        try:
            photo = _tk.PhotoImage(file=gif_path)
            splash_frames.append(photo)
            w, h = photo.width(), photo.height()
            if w > MAX_SPLASH_W or h > MAX_SPLASH_H:
                r = min(MAX_SPLASH_W / w, MAX_SPLASH_H / h)
                splash_w, splash_h = int(w * r), int(h * r)
            else:
                splash_w, splash_h = w, h
        except Exception:
            pass

    screen_w = splash_root.winfo_screenwidth()
    screen_h = splash_root.winfo_screenheight()
    x = max(0, (screen_w - splash_w) // 2)
    y = max(0, (screen_h - splash_h) // 2)
    splash_root.geometry(f'{splash_w}x{splash_h}+{x}+{y}')
    splash_root.resizable(False, False)

    # Pack dot bar first so it stays fixed at the bottom; then GIF fills the rest above it
    DOT_COLORS = ('#0d0d0d', '#1a0a2e', '#3d1a5c', '#9333ea', '#3d1a5c', '#1a0a2e')
    NUM_DOTS = 12
    dot_bar = _tk.Frame(splash_root, bg='#000000', height=56)
    dot_bar.pack(side='bottom', fill='x', padx=0, pady=0)
    dot_bar.pack_propagate(False)
    dot_inner = _tk.Frame(dot_bar, bg='#000000')
    dot_inner.pack(expand=True)
    dot_labels = []
    for i in range(NUM_DOTS):
        lb = _tk.Label(dot_inner, text='\u2022', bg='#000000', fg=DOT_COLORS[0], font=('Segoe UI', 24, 'bold'), relief='flat')
        lb.pack(side='left', padx=5)
        dot_labels.append(lb)
    dot_phase = [0]
    DOT_ANIM_MS = 90
    splash_closed = [False]
    tick_dots_after_id = [None]
    show_frame_after_id = [None]

    def tick_dots():
        if splash_closed[0]:
            return
        try:
            if not splash_root.winfo_exists():
                return
        except Exception:
            return
        dot_phase[0] = (dot_phase[0] + 1) % len(DOT_COLORS)
        for i, lb in enumerate(dot_labels):
            idx = (dot_phase[0] + i) % len(DOT_COLORS)
            c = DOT_COLORS[idx]
            lb.configure(fg=c)
        if not splash_closed[0]:
            try:
                tick_dots_after_id[0] = splash_root.after(DOT_ANIM_MS, tick_dots)
            except Exception:
                pass

    tick_dots_after_id[0] = splash_root.after(DOT_ANIM_MS, tick_dots)

    label = _tk.Label(splash_root, image=None, bg='#000000')
    label.pack(side='top', fill='both', expand=True)
    splash_current = [0]
    splash_refs = [splash_frames]

    def show_frame():
        if splash_closed[0] or not splash_refs[0]:
            return
        try:
            if not splash_root.winfo_exists():
                return
        except Exception:
            return
        idx = splash_current[0] % len(splash_refs[0])
        label.configure(image=splash_refs[0][idx])
        label.image = splash_refs[0][idx]
        splash_current[0] += 1
        if not splash_closed[0]:
            try:
                show_frame_after_id[0] = splash_root.after(frame_delay_ms, show_frame)
            except Exception:
                pass

    if splash_frames:
        label.configure(image=splash_frames[0])
        label.image = splash_frames[0]
        show_frame_after_id[0] = splash_root.after(frame_delay_ms, show_frame)
    else:
        label.configure(text='Loading...', fg='#9333ea', font=('Segoe UI', 16, 'bold'))

    splash_root.deiconify()
    splash_root.update_idletasks()
    # Re-hide console in case it appears when Tk or py launcher creates it (cancel these before closing splash)
    console_hide_after_ids = []
    for _ms in (100, 300, 600, 1200):
        console_hide_after_ids.append(splash_root.after(_ms, _hide_console_window))

    SPLASH_MIN_MS = 4200

    def close_splash_and_run_app():
        splash_closed[0] = True
        try:
            try:
                if tick_dots_after_id[0] is not None:
                    splash_root.after_cancel(tick_dots_after_id[0])
                    tick_dots_after_id[0] = None
                if show_frame_after_id[0] is not None:
                    splash_root.after_cancel(show_frame_after_id[0])
                    show_frame_after_id[0] = None
                for _aid in console_hide_after_ids:
                    try:
                        splash_root.after_cancel(_aid)
                    except Exception:
                        pass
            except Exception:
                pass

            try:
                splash_root.destroy()
            except Exception:
                pass

            _root = _tk.Tk()
            _root.withdraw()
            _app = AutoBEApp(_root)
            _signal_post_update_health_if_requested()
            for _ms in (0, 200, 600):
                _root.after(_ms, _hide_console_window)
            _root.mainloop()
        except Exception:
            import traceback
            tb = traceback.format_exc()
            try:
                print(tb, flush=True)
            except Exception:
                pass
            try:
                _messagebox.showerror("AutoBE startup error", tb)
            except Exception:
                pass

    splash_root.after(SPLASH_MIN_MS, close_splash_and_run_app)
    splash_root.mainloop()


def strip_bom(text):
    # Remove Unicode BOM
    if text.startswith('\ufeff'):
        text = text[1:]
    # Remove UTF-8 BOM interpreted as latin-1 (ï»¿)
    if text.startswith('ï»¿'):
        text = text[3:]
    return text

def read_text_file_utf8_strip_bom(path):
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    if text.startswith('\ufeff'):
        text = text[1:]
    return text

def write_text_file_utf8(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def _signal_post_update_health_if_requested():
    """Write post-update marker only after app has initialized successfully."""
    try:
        if "--post-update-check" not in sys.argv:
            return
        _idx = sys.argv.index("--post-update-check")
        if _idx + 1 >= len(sys.argv):
            return
        _marker_path = sys.argv[_idx + 1]
        if not _marker_path:
            return
        with open(_marker_path, "w", encoding="utf-8") as _mf:
            _mf.write("ok\n")
    except Exception:
        pass

def _get_update_result_fallback_path():
    """Stable per-user update result file (survives temp cleanup)."""
    try:
        base = _os.environ.get("LOCALAPPDATA") or _tempfile.gettempdir()
        folder = _os.path.join(base, "AutoBE")
        _os.makedirs(folder, exist_ok=True)
        return _os.path.join(folder, "update_result_pending.txt")
    except Exception:
        return _os.path.join(_tempfile.gettempdir(), "AutoBE_update_result_pending.txt")

def _read_and_remove_update_result_file(path):
    try:
        if not path or not _os.path.isfile(path):
            return None
        with open(path, "r", encoding="utf-8", errors="ignore") as _rf:
            _status = (_rf.read() or "").strip()
        try:
            _os.remove(path)
        except Exception:
            pass
        return _status or None
    except Exception:
        return None

def _consume_post_update_result_arg():
    """Read one-shot updater result marker and return status string."""
    try:
        # Prefer stable fallback file first so manual app restarts still show result.
        _fallback = _read_and_remove_update_result_file(_get_update_result_fallback_path())
        if _fallback:
            return _fallback
        if "--post-update-result" not in sys.argv:
            return None
        _idx = sys.argv.index("--post-update-result")
        if _idx + 1 >= len(sys.argv):
            return None
        _result_path = sys.argv[_idx + 1]
        if not _result_path:
            return None
        if not _os.path.isfile(_result_path):
            # Fallback: updater passed the arg but marker is missing
            # (temp cleanup/AV race). Treat as success so users still
            # get a completion notice instead of silence.
            return "UPDATED_OK"
        return _read_and_remove_update_result_file(_result_path)
    except Exception:
        return None

if __name__ == "__main__":
    try:
        try:
            print("Starting AutoBE...", flush=True)
        except Exception:
            pass
        # Only hide console automatically when running as a packaged executable.
        if getattr(sys, "frozen", False):
            _hide_console_window()
        _run_splash_then_app()
    except Exception:
        import traceback
        tb = traceback.format_exc()
        try:
            print(tb, flush=True)
        except Exception:
            pass
        try:
            _messagebox.showerror("AutoBE fatal error", tb)
        except Exception:
            pass
