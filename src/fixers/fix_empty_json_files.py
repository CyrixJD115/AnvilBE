"""
Fixes addon files that are empty JSON objects {}.
Bedrock rejects these with errors like:
  [Recipes][error]  - Missing version tag
  [Recipes][error]  - JSON: X has no identifier
  [Animation][error]- ill-formatted/missing "format_version" field. Skipping.

The creator left placeholder files (empty {}) in the pack. The fix is to
replace them with a minimal valid skeleton so Bedrock silently ignores them
instead of logging errors.
"""

import json
TARGETS = ["*.mcpack", "*.mcaddon"]
DESCRIPTION = "Replace empty {} placeholder JSON files with valid minimal skeletons"

_RECIPE_SKELETON    = {"format_version": "1.12.0"}
_ANIM_CTRL_SKELETON = {"format_version": "1.10.0", "animation_controllers": {}}


def fix(pack_name, filepath, content):
    if not filepath.endswith(".json"):
        return None
    try:
        data = json.loads(content.decode("utf-8", errors="ignore"))
    except Exception:
        return None
    if data:
        return None

    fp = filepath.replace('\\', '/')
    if '/recipes/' in fp or fp.startswith('recipes/'):
        return json.dumps(_RECIPE_SKELETON, indent=2).encode("utf-8")

    if '/animation_controllers/' in fp or fp.startswith('animation_controllers/'):
        return json.dumps(_ANIM_CTRL_SKELETON, indent=2).encode("utf-8")

    return None
