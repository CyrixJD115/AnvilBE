"""
Relocate animation controller files that were mistakenly placed under
``render_controllers/``.

Bedrock rejects these with:
  [Rendering][error] - child 'animation_controllers' not valid here.

The file content is valid — it just sits in the wrong folder.
This fixer detects the mismatch by inspecting the JSON root key and, when it
finds ``animation_controllers`` under ``render_controllers/``, returns a new
path under ``animation_controllers/``.
"""

from __future__ import annotations

import json as _json_module

TARGETS = ["*.mcpack", "*.mcaddon"]
DESCRIPTION = "Move animation_controllers files misplaced inside render_controllers/"


# ── Public API ─────────────────────────────────────────────────────────────

def fix(pack_name: str, filepath: str, content: bytes) -> tuple[str, bytes] | None:
    """Return ``(new_path, content)`` when a misplacement is detected, else ``None``.

    Note: unlike most fixers, this returns a **relocation tuple** so the merge
    pipeline knows *where* to write the file.
    """
    if not filepath.startswith("render_controllers/") or not filepath.endswith(".json"):
        return None

    try:
        payload = _json_module.loads(content.decode("utf-8", errors="ignore"))
    except Exception:
        return None

    if "animation_controllers" not in payload:
        return None

    new_path = "animation_controllers/" + filepath[len("render_controllers/"):]
    return (new_path, content)