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

