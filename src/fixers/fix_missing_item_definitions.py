"""
Generate missing BP item definitions and clean up stale RP item files.

Two concerns handled:

  1. **Missing BP item definitions** — any custom item that appears as a
     recipe result but lacks a corresponding ``items/<name>.json`` in the
     behaviour pack gets a minimal definition.  Items already covered by block
     definitions (``fix_missing_block_definitions``) are skipped.

  2. **Stale RP item files** — resource-pack item definitions using the old
     pre-1.16 format (``"1.10"`` / ``"1.10.0"``) are replaced with ``{}`` when
     a modern BP definition exists; leftover RP files confuse the Bedrock
     validator:
       [Item][error] - Resource pack has item definitions not found in BP.

Operates at the **pack level** (``fix_pack``).
"""

from __future__ import annotations

import json as _json_module
from typing import Iterator

TARGETS = ["*.mcpack", "*.mcaddon"]
DESCRIPTION = "Create missing BP item definitions for recipe results; remove obsolete RP item files"

_OBSOLETE_RP_VERSIONS = frozenset({"1.10", "1.10.0"})


# ── Internal helpers ───────────────────────────────────────────────────────

def _matching_paths(names: list[str], subdir: str, suffix: str = ".json") -> Iterator[str]:
    """Yield paths under *subdir* that end with *suffix*."""
    for n in names:
        if subdir in n and n.endswith(suffix):
            yield n


def _collect_ids(names: list[str], archive: "zipfile.ZipFile") -> set[str]:
    """Collect identifiers from ``items/`` and ``blocks/`` definitions."""
    ids: set[str] = set()
    for subdir in ("/items/", "/blocks/"):
        for path in _matching_paths(names, subdir):
            try:
                obj = _json_module.loads(
                    archive.read(path).decode("utf-8", errors="ignore")
                )
                desc = (obj.get("minecraft:item") or obj.get("minecraft:block") or {}).get("description", {})
                iid = desc.get("identifier", "")
                if iid:
                    ids.add(iid)
            except Exception:
                pass
    return ids


def _rp_block_ids(names: list[str], archive: "zipfile.ZipFile") -> set[str]:
    """Collect custom block identifiers from the RP ``blocks.json`` (flat file)."""
    ids: set[str] = set()
    for path in names:
        if path.rsplit("/", 1)[-1] == "blocks.json" and "/blocks/" not in path:
            try:
                obj = _json_module.loads(
                    archive.read(path).decode("utf-8", errors="ignore")
                )
                if isinstance(obj, dict):
                    for bid in obj:
                        if ":" in bid and not bid.startswith("minecraft:"):
                            ids.add(bid)
            except Exception:
                pass
            break
    return ids


def _recipe_result_ids(names: list[str], archive: "zipfile.ZipFile") -> set[str]:
    """Collect non-vanilla item identifiers used as recipe results."""
    ids: set[str] = set()
    _RECIPE_KEYS = (
        "minecraft:recipe_shaped",
        "minecraft:recipe_shapeless",
        "minecraft:recipe_furnace",
        "minecraft:recipe_brewing_mix",
        "minecraft:recipe_brewing_container",
    )

    for path in _matching_paths(names, "/recipes/"):
        try:
            obj = _json_module.loads(
                archive.read(path).decode("utf-8", errors="ignore")
            )
        except Exception:
            continue

        for rkey in _RECIPE_KEYS:
            recipe = obj.get(rkey, {})
            result = recipe.get("result", {})
            if isinstance(result, dict):
                iid = result.get("item", "")
                if iid and ":" in iid and not iid.startswith("minecraft:"):
                    ids.add(iid)
            elif isinstance(result, list):
                for entry in result:
                    iid = entry.get("item", "") if isinstance(entry, dict) else ""
                    if iid and ":" in iid and not iid.startswith("minecraft:"):
                        ids.add(iid)
    return ids


# ── Pack-level API ─────────────────────────────────────────────────────────

def fix_pack(pack_basename: str, archive: "zipfile.ZipFile") -> dict | None:
    """Return ``{"bp": {...}, "rp": {...}}`` with new / removed files, or ``None``."""
    names = archive.namelist()

    bp_ids = _collect_ids(names, archive)
    rp_block_ids = _rp_block_ids(names, archive)
    recipe_ids = _recipe_result_ids(names, archive)

    new_bp: dict[str, bytes] = {}
    empty_rp: dict[str, bytes] = {}

    # ── 1. Generate missing BP item definitions ────────────────────────
    for item_id in recipe_ids:
        if item_id in bp_ids or item_id in rp_block_ids:
            continue
        _ns, item_name = item_id.split(":", 1)
        skeleton = {
            "format_version": "1.16.100",
            "minecraft:item": {
                "description": {
                    "identifier": item_id,
                    "category": "Nature",
                },
                "components": {},
            },
        }
        safe = item_name.replace(":", "_")
        new_bp[f"items/{_ns}_{safe}.json"] = _json_module.dumps(skeleton, indent=2).encode("utf-8")

    # ── 2. Nullify obsolete RP item files backed by modern BP definitions ──
    for path in _matching_paths(names, "/items/"):
        try:
            obj = _json_module.loads(
                archive.read(path).decode("utf-8", errors="ignore")
            )
        except Exception:
            continue

        fmt = str(obj.get("format_version", ""))
        iid = (obj.get("minecraft:item") or {}).get("description", {}).get("identifier", "")
        if fmt in _OBSOLETE_RP_VERSIONS and iid and iid in bp_ids:
            rp_rel = "items/" + path.rsplit("/items/", 1)[-1]
            empty_rp[rp_rel] = b"{}"

    if not new_bp and not empty_rp:
        return None

    return {"rp": empty_rp, "bp": new_bp}