"""
ExtendedBE — per-addon patch loader for AutoBE.

Each module in this package is a "fixer" that selectively patches files inside
addon packs during the merge pipeline.  Patches target bugs or outdated content
*within* the addon itself (not merge-related issues).

Module contract
───────────────
Every fixer module must expose:

    TARGETS : list[str]
        fnmatch glob pattern(s) matched against the source .mcpack basename.

    def fix(pack_name: str, filepath: str, content: bytes) -> bytes | None:
        Return modified bytes to replace *content*, or *None* to leave unchanged.

    def fix_pack(pack_name: str, zip_file: ZipFile) -> dict | None:
        Return a dict ``{"rp": {...}, "bp": {...}}`` mapping output paths to
        new file bytes, or *None* for no pack-level changes.

Optional:

    DESCRIPTION : str
        Short description logged when a fix is applied.
"""

from __future__ import annotations

import importlib.util as _importlib_util
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from types import ModuleType


# ── Public loader ─────────────────────────────────────────────────────────

def load_fixers(fixer_dir: str | None = None) -> list[ModuleType]:
    """Scan *fixer_dir* and import every ``.py`` module with ``TARGETS`` + ``fix``/``fix_pack``.

    Returns a list of loaded module objects ready to be called by the merge
    pipeline.  Modules starting with ``_`` or named ``__init__`` are skipped.
    """
    if fixer_dir is None:
        fixer_dir = os.path.dirname(os.path.abspath(__file__))

    fixers: list[ModuleType] = []

    try:
        entries = sorted(os.listdir(fixer_dir))
    except Exception:
        return fixers

    for fname in entries:
        if fname.startswith("_") or not fname.endswith(".py"):
            continue

        module_path = os.path.join(fixer_dir, fname)

        try:
            spec = _importlib_util.spec_from_file_location(
                f"fixers.{fname[:-3]}", module_path
            )
            if spec is None or spec.loader is None:
                continue
            mod = _importlib_util.module_from_spec(spec)
            spec.loader.exec_module(mod)

            if not (_has_valid_targets(mod) and _has_fix(mod)):
                continue

            fixers.append(mod)
        except Exception as exc:
            print(f"[ExtendedBE] Warning: could not load {fname}: {exc}")

    return fixers


# ── Internal helpers ───────────────────────────────────────────────────────

def _has_valid_targets(mod: ModuleType) -> bool:
    """Return *True* when *mod* exposes a non-empty ``TARGETS`` list."""
    targets = getattr(mod, "TARGETS", None)
    return bool(targets)


def _has_fix(mod: ModuleType) -> bool:
    """Return *True* when *mod* exposes a callable ``fix`` or ``fix_pack``."""
    return callable(getattr(mod, "fix", None)) or callable(getattr(mod, "fix_pack", None))


