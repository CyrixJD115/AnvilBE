"""
Fixes any addon that places an animation_controllers file inside the
render_controllers/ folder. Bedrock rejects these with:

  [Rendering][error] - child 'animation_controllers' not valid here.

The file content is correct — it just lives in the wrong folder.
This fixer detects the mismatch by peeking at the JSON root key and
moves the file to animation_controllers/ where Bedrock expects it.
"""

import json as _json

TARGETS = ["*.mcpack", "*.mcaddon"]
DESCRIPTION = "Move animation_controllers files misplaced inside render_controllers/"


def fix(pack_name, filepath, content):
    if not filepath.startswith("render_controllers/") or not filepath.endswith(".json"):
        return None
    try:
        data = _json.loads(content.decode("utf-8", errors="ignore"))
    except Exception:
        return None
    if "animation_controllers" not in data:
        return None
    new_path = "animation_controllers/" + filepath[len("render_controllers/"):]
    return (new_path, content)
