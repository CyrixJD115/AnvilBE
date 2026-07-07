"""
Pack-level + per-file fixer: populates empty animation_controllers RP files by
cross-referencing the entity's client file to discover which controller IDs
are actually required.

Bedrock errors silenced:
  [Animation][error] - Required child controller.animation.[...] not found

Root cause: original addon ships {} placeholder animation_controllers files.
Bedrock can find the file but finds no controller definitions inside it.

Algorithm:
  fix_pack() scans all JSON files in the source pack for
  "minecraft:client_entity".description.animations, collects every value that
  starts with "controller.animation.", and stores the populated bytes in a
  module-level dict keyed by the stripped RP path.

  fix() is then called per-file by _copy_to_zip.  When the path matches a
  pending stub it returns the populated bytes, replacing the empty placeholder
  in-place before it is written to the merged ZIP.

  Using fix() avoids the duplicate-entry problem that arises when fix_pack()
  injects a second copy — Bedrock can read the first (empty) entry instead of
  the injected one.
"""

import json
import re
import logging
TARGETS = ["*.mcpack", "*.mcaddon"]
DESCRIPTION = "Stub out empty animation_controllers files from entity client file refs"

# Populated by fix_pack(), consumed by fix().  Cleared at the start of each
# fix_pack() call so stale data from a previous pack never leaks.
_pending_stubs = {}  # stripped_rp_path -> bytes


def fix_pack(pack_basename, zip_file):
    global _pending_stubs
    _pending_stubs.clear()

    names = zip_file.namelist()

    # ── Step 1: collect controller IDs from every entity client file ──────────
    entity_ctrls = {}  # stem (str) -> frozenset of controller ID strings

    for name in names:
        if not name.endswith(".json"):
            continue
        try:
            d = json.loads(zip_file.read(name).decode("utf-8", errors="ignore"))
        except Exception:
            continue

        if not isinstance(d, dict):
            continue
        ce = d.get("minecraft:client_entity")
        if not isinstance(ce, dict):
            continue

        desc = ce.get("description", {})
        animations = desc.get("animations", {}) if isinstance(desc, dict) else {}
        if not isinstance(animations, dict):
            continue

        ctrl_ids = frozenset(
            v for v in animations.values()
            if isinstance(v, str) and v.startswith("controller.animation.")
        )
        if not ctrl_ids:
            continue

        # Key 1: file stem  (e.g. "R/entity/sb_iron_golem.json" → "sb_iron_golem")
        file_stem = re.sub(r"\.entity\.json$|\.json$", "", name.rsplit("/", 1)[-1])
        entity_ctrls[file_stem] = entity_ctrls.get(file_stem, frozenset()) | ctrl_ids

        # Key 2: identifier-derived name  ("sb:iron_golem" → "sb_iron_golem")
        identifier = desc.get("identifier", "") if isinstance(desc, dict) else ""
        if ":" in identifier:
            id_stem = identifier.replace(":", "_")
            entity_ctrls[id_stem] = entity_ctrls.get(id_stem, frozenset()) | ctrl_ids

    if not entity_ctrls:
        return None

    # ── Step 2: find empty animation_controllers files, build stub bytes ──────
    for name in names:
        if not name.endswith(".json"):
            continue
        fp = name.replace("\\", "/")
        if "animation_controllers" not in fp:
            continue

        try:
            d = json.loads(zip_file.read(name).decode("utf-8", errors="ignore"))
        except Exception:
            continue

        # Treat empty list [] the same as empty dict {} — both are placeholder files
        if isinstance(d, list):
            if d:  # non-empty list is unexpected, skip
                continue
            is_empty = True
            ac = {}
        elif isinstance(d, dict):
            ac = d.get("animation_controllers")
            is_empty = (d == {}) or (isinstance(ac, dict) and not ac)
        else:
            continue
        if not is_empty:
            continue

        file_base = fp.rsplit("/", 1)[-1]
        stem = re.sub(
            r"\.animation_controllers\.json$|_animation_controllers\.json$|\.json$",
            "", file_base
        )

        ctrls = entity_ctrls.get(stem)
        if not ctrls:
            continue

        ac_out = {
            ctrl_id: {"initial_state": "default", "states": {"default": {}}}
            for ctrl_id in sorted(ctrls)
        }

        out_bytes = json.dumps(
            {"format_version": "1.10.0", "animation_controllers": ac_out},
            indent=2
        ).encode("utf-8")

        # Key without R/B prefix — must match the filepath seen by fix()
        out_path = fp[2:] if fp.startswith(("R/", "B/")) else fp
        _pending_stubs[out_path] = out_bytes

    return None  # stubs are served via fix(), not via pack-level injection


def fix(pack_name, filepath, content):
    fp = filepath.replace("\\", "/")
    stub = _pending_stubs.get(fp)
    if stub is None:
        return None
    logging.info(f"[Fixer] {fp}: {DESCRIPTION} ({len(json.loads(stub.decode())['animation_controllers'])} controllers)")
    return stub
