"""
Per-file fixer: adds a missing description.identifier to recipe files.

Bedrock error silenced:
  [Recipes][error] - JSON: recipes/sb_emerald_gun.json has no identifier

Root cause: old addons shipped recipe files without a description block (or
with a description that has no identifier field).  Modern Bedrock requires
every recipe to have a unique identifier.

Fix: if the recipe JSON has a recognised recipe-type key but its description
is missing or has no identifier, inject one derived from the filename stem.
  e.g.  recipes/sb_emerald_gun.json  →  identifier "sb_emerald_gun"
"""

import json
TARGETS = ["*.mcpack", "*.mcaddon"]
DESCRIPTION = "Add missing description.identifier to recipe files"

_RECIPE_TYPES = {
    "minecraft:recipe_shaped",
    "minecraft:recipe_shapeless",
    "minecraft:recipe_furnace",
    "minecraft:recipe_brewing_mix",
    "minecraft:recipe_brewing_container",
    "minecraft:recipe_material_reduction",
}

# Types that require the unlock field in 1.20+ Bedrock
_UNLOCK_TYPES = {"minecraft:recipe_shaped", "minecraft:recipe_shapeless"}


def fix(pack_name, filepath, content):
    fp = filepath.replace("\\", "/")
    if not fp.endswith(".json"):
        return None
    if not (fp.startswith("recipes/") or "/recipes/" in fp):
        return None

    try:
        data = json.loads(content.decode("utf-8", errors="ignore"))
    except Exception:
        return None

    # Find the recipe type key present in this file
    recipe_body = None
    for rt in _RECIPE_TYPES:
        if rt in data:
            recipe_body = data[rt]
            break

    # File is completely empty {} or has no recipe type key at all —
    # inject a harmless dummy so Bedrock doesn't log "no identifier"
    if not isinstance(recipe_body, dict):
        stem = fp.rsplit("/", 1)[-1][:-5]
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
        return json.dumps(dummy, indent=2).encode("utf-8")

    desc = recipe_body.get("description")
    modified = False

    if not (isinstance(desc, dict) and "identifier" in desc):
        stem = fp.rsplit("/", 1)[-1][:-5]  # strip .json
        if not isinstance(desc, dict):
            recipe_body["description"] = {"identifier": stem}
        else:
            desc["identifier"] = stem
        modified = True

    # Add missing unlock field required by 1.20+ for shaped/shapeless recipes
    found_rt = next((k for k in _UNLOCK_TYPES if k in data), None)
    if found_rt and "unlock" not in recipe_body:
        recipe_body["unlock"] = [{"context": "AlwaysUnlocked"}]
        modified = True

    if not modified:
        return None

    return json.dumps(data, indent=2).encode("utf-8")
