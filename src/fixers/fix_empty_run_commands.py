"""
Eliminate deprecated ``run_command`` from entity event definitions.

Bedrock no longer accepts ``run_command`` inside entity events:
  [Actor][error] - child 'run_command' not valid here.

Two cases are handled:
  1. ``run_command`` with an empty command list — removed outright.
  2. ``run_command`` with actual commands — renamed to ``queue_command``,
     the modern Bedrock equivalent that *is* valid inside events.

Scans the entire event tree, including ``sequence`` and ``randomize`` branches.
"""

from __future__ import annotations

import json as _json_module

TARGETS = ["*.mcpack", "*.mcaddon"]
DESCRIPTION = "Remove empty run_command / rename populated run_command → queue_command in entity events"


# ── Internal helpers ───────────────────────────────────────────────────────

def _purge_run_command(event: dict) -> bool:
    """Strip or rename ``run_command`` inside *event* in place.

    Returns ``True`` when the event was modified.
    """
    if not isinstance(event, dict):
        return False
    if "run_command" not in event:
        return False

    body = event["run_command"]
    if not isinstance(body, dict):
        return False

    if body.get("command") == []:
        # Empty placeholder — strip entirely
        del event["run_command"]
    else:
        # Populated — rename to the modern key
        event["queue_command"] = event.pop("run_command")
    return True


# ── Public API ─────────────────────────────────────────────────────────────

def fix(pack_name: str, filepath: str, content: bytes) -> bytes | None:
    """Return fixed *bytes* or ``None`` when no change is needed."""
    if not filepath.endswith(".json"):
        return None

    normalised = filepath.replace("\\", "/")
    if "/entities/" not in normalised and not normalised.startswith("entities/"):
        return None

    try:
        data = _json_module.loads(content.decode("utf-8", errors="ignore"))
    except Exception:
        return None

    events: dict = (data.get("minecraft:entity") or {}).get("events") or {}
    if not isinstance(events, dict):
        return None

    touched = False
    for event_body in events.values():
        if not isinstance(event_body, dict):
            continue

        if _purge_run_command(event_body):
            touched = True

        # Recurse into sequence / randomize arrays
        for group_key in ("sequence", "randomize"):
            for entry in event_body.get(group_key, []):
                if _purge_run_command(entry):
                    touched = True

    if not touched:
        return None

    return _json_module.dumps(data, indent=2).encode("utf-8")