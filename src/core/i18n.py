"""
Internationalization (i18n) system for Anvil-MC.
Loads JSON locale files and provides translation lookup functions.
"""
import os as _os
import json as _json
import sys as _sys

_TRANSLATIONS = {}
_CURRENT_LANG = "en"

# Determine the base directory (works for both source and frozen builds)
_BASE_DIR = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
_LOCALE_DIR = _os.path.join(_BASE_DIR, "locales")


def _tr_load(lang):
    """Load a locale JSON into the translations cache. Falls back to 'en' if missing."""
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
    """Return the translation for *key*, or *key* itself if not found."""
    return _TRANSLATIONS.get(key, key)


def _f(key, **kwargs):
    """Return a formatted translation with placeholders filled (e.g. {version})."""
    return _(key).format(**kwargs)


def _parse_lang_kv(text):
    """Parse Minecraft .lang key=value format into a dict."""
    out = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if '=' not in line:
            continue
        k, v = line.split('=', 1)
        k = k.strip()
        if not k:
            continue
        out[k] = v.strip()
    return out


def _get_tos_text():
    """Load Terms of Service text from locales/tos_{lang}.txt."""
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
    """Initialize translations with the default language (English)."""
    global _CURRENT_LANG
    _tr_load("en")
