"""
Inject a ``description.identifier`` into recipe files that lack one.

Bedrock error silenced:
  [Recipes][error] - JSON: recipes/sb_emerald_gun.json has no identifier

Old addons shipped recipe files without a description block (or with a
description that omits the identifier field).  Modern Bedrock requires every
recipe to carry a unique identifier.

When the file is completely empty or lacks any recognised recipe-type key,
a harmless dummy recipe is injected so Bedrock doesn't log an error.
"""

from __future__ import annotations

import json as _json_module

TARGETS = ["*.mcpack", "*.mcaddon"]
DESCRIPTION = "Add missing description.identifier to recipe files"

_RECIPE_TYPES = frozenset({
    "minecraft:recipe_shaped",
    "minecraft:recipe_shapeless",
    "minecraft:recipe_furnace",
    "minecraft:recipe_brewing_mix",
    "minecraft:recipe_brewing_container",
    "minecraft:recipe_material_reduction",
})

_TYPES_NEEDING_UNLOCK = frozenset({"minecraft:recipe_shaped", "minecraft:recipe_shapeless"})


# ── Internal helpers ───────────────────────────────────────────────────────

def _stem_from_path(fp: str) -> str:
    """Extract the filename stem (without ``.json``) from a forward-slash path."""
    return fp.rsplit("/", 1)[-1][:-5]


def _build_dummy_recipe(stem: str) -> bytes:
    """Return a harmless shapeless recipe that prevents Bedrock errors."""
    dummy = {
        "format_version": "1.21.0",
        "minecraft:recipe_shapeless": {
            "description": {"identifier": stem},
            "tags": ["crafting_table"],
            "ingredients": [{"item": "minecraft:stick"}],
            "result": {"item": "minecraft:stick"},
            "unlock": [{"context": "AlwaysUnlocked"}],
        },
    }
    return _json_module.dumps(dummy, indent=2).encode("utf-8")


# ── Public API ─────────────────────────────────────────────────────────────

def fix(pack_name: str, filepath: str, content: bytes) -> bytes | None:
    """Return updated *bytes* with identifier injected, or ``None``."""
    normalised = filepath.replace("\\", "/")
    if not normalised.endswith(".json"):
        return None
    if not (normalised.startswith("recipes/") or "/recipes/" in normalised):
        return None

    try:
        data = _json_module.loads(content.decode("utf-8", errors="ignore"))
    except Exception:
        return None

    # Identify which recipe type key is present
    recipe_body = None
    for rt in _RECIPE_TYPES:
        if rt in data:
            recipe_body = data[rt]
            break

    # File is empty {} or has no recognised recipe type — inject dummy.
    if not isinstance(recipe_body, dict):
        return _build_dummy_recipe(_stem_from_path(normalised))

    desc = recipe_body.get("description")
    modified = False

    if not (isinstance(desc, dict) and "identifier" in desc):
        stem = _stem_from_path(normalised)
        if not isinstance(desc, dict):
            recipe_body["description"] = {"identifier": stem}
        else:
            desc["identifier"] = stem
        modified = True

    # Inject the ``unlock`` field required by 1.20+ for shaped / shapeless recipes.
    found = next((k for k in _TYPES_NEEDING_UNLOCK if k in data), None)
    if found is not None and "unlock" not in recipe_body:
        recipe_body["unlock"] = [{"context": "AlwaysUnlocked"}]
        modified = True

    if not modified:
        return None

    return _json_module.dumps(data, indent=2).encode("utf-8")