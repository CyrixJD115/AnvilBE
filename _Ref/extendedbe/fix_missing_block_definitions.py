"""
Pack-level fixer: creates minimal BP block definitions for any custom block
that appears in the RP blocks.json but has no matching definition in the
BP blocks/ folder.

Bedrock errors this silences:
  [Texture][warning]  - The block named X used in a "blocks.json" file does not
                        exist in the registry
  [Recipes][error]    - The Item: X is missing or invalid, can't make the recipe
  [Recipes][error]    - Recipe result malformed

Root cause: the addon was created in the old Bedrock era when custom blocks
only needed a blocks.json entry in the RP. Modern Bedrock requires every
custom block to also have a behavior-pack definition in blocks/<name>.json.
This fixer auto-generates the minimal skeleton so Bedrock registers the block.
"""

import json as _json

TARGETS = ["*.mcpack", "*.mcaddon"]
DESCRIPTION = "Create missing BP block definitions for blocks declared in RP blocks.json"


def fix_pack(pack_basename, zip_file):
    names = list(zip_file.namelist())

    # Find the RP blocks.json regardless of folder prefix.
    # It is a flat file (not inside a blocks/ subfolder) so we match by filename only.
    rp_blocks_path = None
    for name in names:
        base = name.rsplit('/', 1)[-1]
        if base == 'blocks.json' and '/blocks/' not in name:
            rp_blocks_path = name
            break
    if not rp_blocks_path:
        return None

    try:
        rp_blocks = _json.loads(zip_file.read(rp_blocks_path).decode('utf-8', errors='ignore'))
    except Exception:
        return None
    if not isinstance(rp_blocks, dict):
        return None

    # Find existing BP block definitions — any .json inside a blocks/ subfolder
    # whose content has a minecraft:block key.
    existing_block_ids = set()
    for name in names:
        if '/blocks/' not in name or not name.endswith('.json'):
            continue
        try:
            d = _json.loads(zip_file.read(name).decode('utf-8', errors='ignore'))
            bid = (d.get('minecraft:block') or {}).get('description', {}).get('identifier', '')
            if bid:
                existing_block_ids.add(bid)
        except Exception:
            pass

    new_bp_files = {}
    for block_id in rp_blocks:
        if ':' not in block_id or block_id.startswith('minecraft:'):
            continue
        if block_id in existing_block_ids:
            continue
        namespace, block_name = block_id.split(':', 1)
        block_def = {
            "format_version": "1.19.0",
            "minecraft:block": {
                "description": {
                    "identifier": block_id
                },
                "components": {}
            }
        }
        safe_name = block_name.replace(':', '_')
        file_path = f"blocks/{namespace}_{safe_name}.json"
        new_bp_files[file_path] = _json.dumps(block_def, indent=2).encode('utf-8')

    if not new_bp_files:
        return None
    return {'rp': {}, 'bp': new_bp_files}
