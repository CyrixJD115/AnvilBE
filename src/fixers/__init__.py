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

import os
import importlib.util as _importlib_util


def load_fixers(extendedbe_dir=None):
    """
    Scan the extendedbe directory and import every .py fixer module.
    Returns a list of loaded module objects that have a valid fix() callable
    and a non-empty TARGETS list.
    """
    if extendedbe_dir is None:
        extendedbe_dir = os.path.dirname(os.path.abspath(__file__))

    fixers = []
    try:
        for fname in sorted(os.listdir(extendedbe_dir)):
            if fname.startswith('_') or not fname.endswith('.py'):
                continue
            fpath = os.path.join(extendedbe_dir, fname)
            try:
                spec = _importlib_util.spec_from_file_location(
                    f'fixers.{fname[:-3]}', fpath)
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
