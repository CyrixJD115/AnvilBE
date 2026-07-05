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
