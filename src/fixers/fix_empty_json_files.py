"""
Replace empty JSON placeholder files (``{}``) with minimal valid skeletons.

Bedrock rejects empty ``{}`` JSON files, logging errors such as:
  [Recipes][error]   - Missing version tag
  [Animation][error] - ill-formatted/missing "format_version" field

The fix detects an empty object and, based on the location of the file within
the pack, writes a skeleton that Bedrock will silently accept.
"""

from __future__ import annotations

import json as _json_module

TARGETS = ["*.mcpack", "*.mcaddon"]
DESCRIPTION = "Replace empty {} placeholder JSON files with valid minimal skeletons"

# ── Skeleton templates ─────────────────────────────────────────────────────
_RECIPE_BLANK    = {"format_version": "1.12.0"}
_ANIM_CTRL_BLANK = {"format_version": "1.10.0", "animation_controllers": {}}


# ── Public API ─────────────────────────────────────────────────────────────

def fix(pack_name: str, filepath: str, content: bytes) -> bytes | None:
    """Return skeleton *bytes* if *content* is empty JSON, otherwise ``None``."""
    if not filepath.endswith(".json"):
        return None

    try:
        payload = _json_module.loads(content.decode("utf-8", errors="ignore"))
    except Exception:
        return None

    # Non-empty — nothing to fix
    if payload:
        return None

    normalised = filepath.replace("\\", "/")

    if "/recipes/" in normalised or normalised.startswith("recipes/"):
        return _json_module.dumps(_RECIPE_BLANK, indent=2).encode("utf-8")

    if "/animation_controllers/" in normalised or normalised.startswith("animation_controllers/"):
        return _json_module.dumps(_ANIM_CTRL_BLANK, indent=2).encode("utf-8")

    return None