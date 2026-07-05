"""
Fixes entity behavior files that use the deprecated run_command action in events.
Bedrock rejects run_command in entity events with:
  [Actor][error] - child 'run_command' not valid here.

Two fixes applied:
  1. run_command with an empty command list (command:[]) — removed entirely.
  2. run_command with actual commands — renamed to queue_command, the modern
     Bedrock replacement that IS valid in entity events.
"""

import json as _json

TARGETS = ["*.mcpack", "*.mcaddon"]
DESCRIPTION = "Fix run_command in entity events: remove empty, rename non-empty to queue_command"


def _fix_event(event):
    """Fix run_command in an event dict. Returns (event, changed)."""
    if not isinstance(event, dict):
        return event, False
    if "run_command" not in event:
        return event, False
    rc = event["run_command"]
    if not isinstance(rc, dict):
        return event, False
    if rc.get("command") == []:
        # Empty placeholder — remove entirely
        del event["run_command"]
    else:
        # Non-empty — rename to queue_command (modern replacement)
        event["queue_command"] = event.pop("run_command")
    return event, True


def fix(pack_name, filepath, content):
    if not filepath.endswith(".json"):
        return None
    fp = filepath.replace('\\', '/')
    if '/entities/' not in fp and not fp.startswith('entities/'):
        return None
    try:
        data = _json.loads(content.decode("utf-8", errors="ignore"))
    except Exception:
        return None

    events = (data.get("minecraft:entity") or {}).get("events") or {}
    if not isinstance(events, dict):
        return None

    changed = False
    for event_name, event_body in events.items():
        if not isinstance(event_body, dict):
            continue
        _, c = _fix_event(event_body)
        if c:
            changed = True
        # check inside sequence and randomize arrays
        for arr_key in ("sequence", "randomize"):
            for entry in event_body.get(arr_key, []):
                _, c = _fix_event(entry)
                if c:
                    changed = True

    if not changed:
        return None
    return _json.dumps(data, indent=2).encode("utf-8")
