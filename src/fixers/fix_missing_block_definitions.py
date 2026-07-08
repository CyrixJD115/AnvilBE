"""
Generate minimal behaviour-pack block definitions for custom blocks declared
in the resource-pack ``blocks.json``.

Bedrock errors silenced:
  [Texture][warning] - The block named X used in a "blocks.json" file does not
                       exist in the registry
  [Recipes][error]   - The Item: X is missing or invalid, can't make the recipe

Root cause: addons created in the old Bedrock era only needed a ``blocks.json``
entry in the RP.  Modern Bedrock requires every custom block to also carry a
behaviour-pack definition under ``blocks/<name>.json``.

This fixer operates at the **pack level** (``fix_pack``) — it reads the RP
``blocks.json``, cross-references existing BP block definitions, and emits any
that are missing.
"""

from __future__ import annotations

import json as _json_module

TARGETS = ["*.mcpack", "*.mcaddon"]
DESCRIPTION = "Create missing BP block definitions for blocks declared in RP blocks.json"


# ── Internal helpers ───────────────────────────────────────────────────────

def _locate_rp_blocks_json(names: list[str]) -> str | None:
    """Return the first path matching a top-level ``blocks.json`` (not inside ``blocks/``)."""
    for path in names:
        if path.rsplit("/", 1)[-1] == "blocks.json" and "/blocks/" not in path:
            return path
    return None


def _existing_block_ids(names: list[str], archive: "zipfile.ZipFile") -> set[str]:
    """Collect every block identifier already defined in ``blocks/`` subdirectories."""
    ids: set[str] = set()
    for path in names:
        if "/blocks/" not in path or not path.endswith(".json"):
            continue
        try:
            obj = _json_module.loads(archive.read(path).decode("utf-8", errors="ignore"))
            bid = (obj.get("minecraft:block") or {}).get("description", {}).get("identifier", "")
            if bid:
                ids.add(bid)
        except Exception:
            pass
    return ids


# ── Pack-level API ─────────────────────────────────────────────────────────

def fix_pack(pack_basename: str, archive: "zipfile.ZipFile") -> dict | None:
    """Return ``{"bp": {path: bytes, ...}}`` for missing block definitions, or ``None``."""
    names = archive.namelist()

    rp_path = _locate_rp_blocks_json(names)
    if rp_path is None:
        return None

    try:
        rp_blocks = _json_module.loads(
            archive.read(rp_path).decode("utf-8", errors="ignore")
        )
    except Exception:
        return None

    if not isinstance(rp_blocks, dict):
        return None

    existing = _existing_block_ids(names, archive)

    new_defs: dict[str, bytes] = {}

    for block_id, _unused in rp_blocks.items():
        if ":" not in block_id or block_id.startswith("minecraft:"):
            continue
        if block_id in existing:
            continue

        _namespace, block_name = block_id.split(":", 1)
        skeleton = {
            "format_version": "1.19.0",
            "minecraft:block": {
                "description": {"identifier": block_id},
                "components": {},
            },
        }
        safe_name = block_name.replace(":", "_")
        file_path = f"blocks/{_namespace}_{safe_name}.json"
        new_defs[file_path] = _json_module.dumps(skeleton, indent=2).encode("utf-8")

    if not new_defs:
        return None

    return {"rp": {}, "bp": new_defs}