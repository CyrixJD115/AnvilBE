"""
ExtendedBE — per-addon patch loader for AutoBE.

Each .py file in this directory is a "fixer" module that targets one or more
specific addon packs and patches their files during the merge process.  These
fixes are for bugs/outdated code IN the addon itself (not merging issues).

AutoBE imports all modules here at startup and calls fix() for every file
inside every matching source pack before it is written to the merged output.

──────────────────────────────────────────────────────────────────────────────
HOW TO WRITE A FIXER
──────────────────────────────────────────────────────────────────────────────
Create a new .py file in this folder, e.g.  my_addon_fix.py

Required variables / functions:

    TARGETS : list[str]
        Glob (fnmatch) patterns matched against the source .mcpack FILENAME
        (basename only, not the full path).
        Example:  TARGETS = ["BrokenAddon_*.mcpack", "OutdatedPack.mcpack"]

    def fix(pack_name: str, filepath: str, content: bytes) -> bytes | None:
        pack_name  – basename of the source .mcpack  (e.g. "BrokenAddon_2.mcpack")
        filepath   – path inside the zip             (e.g. "scripts/main.js")
        content    – raw bytes of the file
        Returns    – modified bytes to replace the file, or None to leave unchanged.

Optional:

    DESCRIPTION : str
        Short human-readable description shown in the AutoBE log.

──────────────────────────────────────────────────────────────────────────────
EXAMPLE
──────────────────────────────────────────────────────────────────────────────
    TARGETS = ["OldWeapons_*.mcpack"]
    DESCRIPTION = "Replace deprecated system.run() with system.runInterval()"

    def fix(pack_name, filepath, content):
        if not filepath.endswith(".js"):
            return None
        text = content.decode("utf-8", errors="ignore")
        if "system.run(" not in text:
            return None
        text = text.replace("system.run(", "system.runTimeout(")
        return text.encode("utf-8")
"""

import os as _os
import importlib.util as _importlib_util
import fnmatch as _fnmatch
import logging as _log


def load_fixers(extendedbe_dir=None):
    """
    Scan the extendedbe directory and import every .py fixer module.
    Returns a list of loaded module objects that have a valid fix() callable
    and a non-empty TARGETS list.
    """
    if extendedbe_dir is None:
        extendedbe_dir = _os.path.dirname(_os.path.abspath(__file__))

    fixers = []
    try:
        for fname in sorted(_os.listdir(extendedbe_dir)):
            if fname.startswith('_') or not fname.endswith('.py'):
                continue
            fpath = _os.path.join(extendedbe_dir, fname)
            try:
                spec = _importlib_util.spec_from_file_location(
                    f'extendedbe.{fname[:-3]}', fpath)
                mod = _importlib_util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                targets = getattr(mod, 'TARGETS', [])
                has_fix = callable(getattr(mod, 'fix', None))
                has_fix_pack = callable(getattr(mod, 'fix_pack', None))
                if targets and (has_fix or has_fix_pack):
                    fixers.append(mod)
            except Exception as e:
                print(f"[ExtendedBE] Warning: could not load {fname}: {e}")
    except Exception:
        pass
    return fixers


def apply_pack_fixers(fixers, pack_basename, zip_file):
    """
    Run pack-level fixers that need to see the full pack content to do their job
    (e.g. detecting recipe results whose item/block definitions are missing).

    Each fixer module may optionally define:

        def fix_pack(pack_basename, zip_file):
            \"\"\"
            zip_file : zipfile.ZipFile open for reading
            Returns  : {"rp": {filepath: bytes}, "bp": {filepath: bytes}}
                       for new/modified files to inject into the merged RP or BP.
                       Return None or {} if nothing to add.
            \"\"\"

    Returns the merged {"rp": {...}, "bp": {...}} dict from all fixers.
    """
    rp_extra, bp_extra = {}, {}
    for mod in fixers:
        targets = getattr(mod, 'TARGETS', [])
        if not any(_fnmatch.fnmatch(pack_basename, pat) for pat in targets):
            continue
        fix_pack_fn = getattr(mod, 'fix_pack', None)
        if not callable(fix_pack_fn):
            continue
        try:
            result = fix_pack_fn(pack_basename, zip_file) or {}
            rp_extra.update(result.get('rp', {}))
            bp_extra.update(result.get('bp', {}))
        except Exception as e:
            desc = getattr(mod, 'DESCRIPTION', mod.__name__)
            print(f"[ExtendedBE] Error in pack fixer '{desc}': {e}")
    return {'rp': rp_extra, 'bp': bp_extra}


def apply_fixers(fixers, pack_basename, filepath, content_bytes):
    """
    Run all loaded fixers against a single file.

    fix() may return:
      - None                  : leave file unchanged
      - bytes                 : replace content, keep original filepath
      - (new_path, bytes)     : replace content AND move file to new_path
      - (new_path, None)      : move file to new_path, keep content unchanged

    Returns (filepath, content_bytes) — filepath may be different from the
    input if a fixer requested a rename/move.
    """
    for mod in fixers:
        targets = getattr(mod, 'TARGETS', [])
        if not any(_fnmatch.fnmatch(pack_basename, pat) for pat in targets):
            continue
        try:
            result = mod.fix(pack_basename, filepath, content_bytes)
            if result is None:
                continue
            desc = getattr(mod, 'DESCRIPTION', mod.__name__)
            if isinstance(result, tuple):
                new_path, new_bytes = result
                changed = (new_path is not None and new_path != filepath) or (new_bytes is not None and new_bytes != content_bytes)
                if new_path is not None:
                    filepath = new_path
                if new_bytes is not None:
                    content_bytes = new_bytes
            else:
                changed = result != content_bytes
                content_bytes = result
            if changed:
                _log.info(f"[Fixer] {filepath}: {desc}")
        except Exception as e:
            desc = getattr(mod, 'DESCRIPTION', mod.__name__)
            print(f"[ExtendedBE] Error in '{desc}' fixing {filepath}: {e}")
    return filepath, content_bytes
