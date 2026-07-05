"""
Internationalization (i18n) system for Anvil-MC.
Loads JSON locale files and provides translation lookup functions.
"""
import os as _os
import json as _json
import sys as _sys

_TRANSLATIONS = {}
_CURRENT_LANG = "en"

# Native display names keyed by locale code. Used for the language picker.
_LANG_NAMES = {
    "en": "English",
    "es": "Español",
    "zh": "中文",
    "id": "Bahasa Indonesia",
    "ru": "Русский",
    "pt": "Português (Brasil)",
    "fr": "Français",
    "de": "Deutsch",
}

# Determine the base directory (works for both source and frozen builds)
_BASE_DIR = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
_LOCALE_DIR = _os.path.join(_BASE_DIR, "locales")


def available_languages():
    """Return a list of (code, display_name) for every locale JSON on disk.

    English is always first; the rest are alphabetical by display name.
    """
    result = []
    try:
        if _os.path.isdir(_LOCALE_DIR):
            for fname in _os.listdir(_LOCALE_DIR):
                if fname.lower().endswith('.json'):
                    code = fname[:-5]
                    result.append((code, _LANG_NAMES.get(code, code)))
    except Exception:
        pass
    result.sort(key=lambda c: (c[0] != "en", c[1]))
    if not result:
        result = [("en", _LANG_NAMES["en"])]
    return result


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


def current_lang():
    """Return the currently active language code (e.g. 'en', 'es')."""
    return _CURRENT_LANG


def help_content_path(lang=None, resources_dir=None):
    """Resolve the best help-content HTML path for *lang*.

    Prefers ``help_content_<lang>.html``; falls back to the base
    ``help_content.html`` (English) when a localized file is absent.
    """
    lang = (lang or _CURRENT_LANG or "en").lower()
    base = _os.path.join(_BASE_DIR, "resources")
    if resources_dir:
        base = resources_dir
    localized = _os.path.join(base, f"help_content_{lang}.html")
    if _os.path.isfile(localized):
        return localized
    return _os.path.join(base, "help_content.html")


def _(key):
    """Return the translation for *key*, or *key* itself if not found."""
    return _TRANSLATIONS.get(key, key)


def _tr(key, fallback=None):
    """Return the translation for *key*, or *fallback* (or *key*) when untranslated."""
    val = _TRANSLATIONS.get(key)
    if val and val != key:
        return val
    return fallback if fallback is not None else key


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


def _init_translations():
    """Initialize translations with the default language (English)."""
    global _CURRENT_LANG
    _tr_load("en")
