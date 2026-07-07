"""
Pack-level fixer: creates minimal BP item definitions for any custom item that
appears in a recipe result but has no corresponding BP items/ definition AND is
not a custom block (those are handled by fix_missing_block_definitions.py).

Also removes stale RP items/ definitions that use the old pre-1.16 format
("1.10" / "1.10.0") when the BP already has a modern definition — they cause
Bedrock to log:
  [Item][error] - Resource pack has item definitions not found in the behavior pack.

Root cause: addons from 2020-2022 placed item client data in RP items/ (old
system). Modern Bedrock dropped this in favour of BP item definitions alone;
the leftover RP items confuse the modern validator.
"""

import json
TARGETS = ["*.mcpack", "*.mcaddon"]
DESCRIPTION = "Create missing BP item definitions for recipe results; remove obsolete RP item files"

_OLD_RP_ITEM_VERSIONS = {"1.10", "1.10.0"}


def _find_all(names, subpath_contains, suffix='.json'):
    """Yield names whose path contains subpath_contains and ends with suffix."""
    for n in names:
        if subpath_contains in n and n.endswith(suffix):
            yield n


def fix_pack(pack_basename, zip_file):
    names = list(zip_file.namelist())

    # Collect all BP-defined item identifiers (any items/ subfolder)
    bp_item_ids = set()
    for name in _find_all(names, '/items/'):
        try:
            d = json.loads(zip_file.read(name).decode('utf-8', errors='ignore'))
            iid = (d.get('minecraft:item') or {}).get('description', {}).get('identifier', '')
            if iid:
                bp_item_ids.add(iid)
        except Exception:
            pass

    # Collect all BP-defined block identifiers (any blocks/ subfolder)
    bp_block_ids = set()
    for name in _find_all(names, '/blocks/'):
        try:
            d = json.loads(zip_file.read(name).decode('utf-8', errors='ignore'))
            bid = (d.get('minecraft:block') or {}).get('description', {}).get('identifier', '')
            if bid:
                bp_block_ids.add(bid)
        except Exception:
            pass

    # Collect custom blocks from RP blocks.json (flat file, not inside a blocks/ folder)
    rp_block_ids = set()
    for name in names:
        base = name.rsplit('/', 1)[-1]
        if base == 'blocks.json' and '/blocks/' not in name:
            try:
                rb = json.loads(zip_file.read(name).decode('utf-8', errors='ignore'))
                if isinstance(rb, dict):
                    for bid in rb:
                        if ':' in bid and not bid.startswith('minecraft:'):
                            rp_block_ids.add(bid)
            except Exception:
                pass
            break

    # Collect all recipe result item IDs using custom namespaces
    recipe_result_ids = set()
    for name in _find_all(names, '/recipes/'):
        try:
            d = json.loads(zip_file.read(name).decode('utf-8', errors='ignore'))
            for recipe_type in ('minecraft:recipe_shaped', 'minecraft:recipe_shapeless',
                                'minecraft:recipe_furnace', 'minecraft:recipe_brewing_mix',
                                'minecraft:recipe_brewing_container'):
                recipe = d.get(recipe_type, {})
                result = recipe.get('result', {})
                if isinstance(result, dict):
                    iid = result.get('item', '')
                    if iid and ':' in iid and not iid.startswith('minecraft:'):
                        recipe_result_ids.add(iid)
                elif isinstance(result, list):
                    for r in result:
                        iid = r.get('item', '') if isinstance(r, dict) else ''
                        if iid and ':' in iid and not iid.startswith('minecraft:'):
                            recipe_result_ids.add(iid)
        except Exception:
            pass

    new_bp_files = {}
    empty_rp_files = {}

    # Create minimal BP item definitions for recipe results not already defined
    for item_id in recipe_result_ids:
        if item_id in bp_item_ids or item_id in bp_block_ids or item_id in rp_block_ids:
            continue
        namespace, item_name = item_id.split(':', 1)
        item_def = {
            "format_version": "1.16.100",
            "minecraft:item": {
                "description": {
                    "identifier": item_id,
                    "category": "Nature"
                },
                "components": {}
            }
        }
        safe_name = item_name.replace(':', '_')
        new_bp_files[f"items/{namespace}_{safe_name}.json"] = json.dumps(item_def, indent=2).encode('utf-8')

    # Remove obsolete old-format RP item definitions that have a modern BP counterpart
    for name in _find_all(names, '/items/'):
        try:
            d = json.loads(zip_file.read(name).decode('utf-8', errors='ignore'))
            fv = str(d.get('format_version', ''))
            iid = (d.get('minecraft:item') or {}).get('description', {}).get('identifier', '')
            if fv in _OLD_RP_ITEM_VERSIONS and iid and iid in bp_item_ids:
                # Strip pack folder prefix — output path is relative to the RP root
                rp_path = 'items/' + name.rsplit('/items/', 1)[-1]
                empty_rp_files[rp_path] = b'{}'
        except Exception:
            pass

    if not new_bp_files and not empty_rp_files:
        return None
    return {'rp': empty_rp_files, 'bp': new_bp_files}
