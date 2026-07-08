"""
Populate placeholder animation-controller files by cross-referencing entity
client files.

Bedrock errors silenced:
  [Animation][error] - Required child controller.animation.[...] not found

Root cause: addon ships ``{}`` or ``[]`` placeholder animation_controller
files.  Bedrock finds the file but discovers no controller definitions.

Algorithm
~~~~~~~~~
:func:`fix_pack` scans every JSON file in the source pack for
``minecraft:client_entity`` → ``description.animations``, collects every value
whose string starts with ``controller.animation.``, then builds fully
populated bytes for each empty ``animation_controllers`` file it finds in the
pack.  Those bytes are cached in a module-global dict keyed by stripped RP
path.

:func:`fix` is called per-file by the merge pipeline.  When the path matches
a pending stub it returns the populated bytes (replacing the empty file
in-place).  Using ``fix()`` avoids the duplicate-entry problem that would arise
if ``fix_pack`` injected the stub as a new file.
"""

from __future__ import annotations

import json as _json_module
import logging as _logging_module
import re as _re_module

TARGETS = ["*.mcpack", "*.mcaddon"]
DESCRIPTION = "Stub out empty animation_controllers files from entity client file refs"

# ── Module-level buffer (set by fix_pack, consumed by fix) ───────────────
_pending: dict[str, bytes] = {}


# ── Internal helpers ───────────────────────────────────────────────────────

def _collect_controller_ids(names: list[str], archive: "zipfile.ZipFile") -> dict[str, frozenset[str]]:
    """Walk every JSON file for entity client data; return ``{stem → frozenset{ctrl_ids}}``."""
    mapping: dict[str, frozenset[str]] = {}

    for name in names:
        if not name.endswith(".json"):
            continue
        try:
            obj = _json_module.loads(
                archive.read(name).decode("utf-8", errors="ignore")
            )
        except Exception:
            continue
        if not isinstance(obj, dict):
            continue

        ce = obj.get("minecraft:client_entity")
        if not isinstance(ce, dict):
            continue

        desc = ce.get("description", {})
        animations = desc.get("animations", {}) if isinstance(desc, dict) else {}
        if not isinstance(animations, dict):
            continue

        ids = frozenset(
            v for v in animations.values()
            if isinstance(v, str) and v.startswith("controller.animation.")
        )
        if not ids:
            continue

        # Key by file stem  (e.g. "R/entity/sb_iron_golem.json" → "sb_iron_golem")
        stem = _re_module.sub(r"\.entity\.json$|\.json$", "", name.rsplit("/", 1)[-1])
        mapping[stem] = mapping.get(stem, frozenset()) | ids

        # Also key by identifier-derived name ("sb:iron_golem" → "sb_iron_golem")
        identifier = desc.get("identifier", "")
        if ":" in identifier:
            id_stem = identifier.replace(":", "_")
            mapping[id_stem] = mapping.get(id_stem, frozenset()) | ids

    return mapping


# ── Pack-level API ─────────────────────────────────────────────────────────

def fix_pack(pack_basename: str, archive: "zipfile.ZipFile") -> None:
    """Scout entity files, compute stub bytes, store in module-level ``_pending``."""
    # Clear stale data from previous pack
    _pending.clear()

    names = archive.namelist()
    ctrl_map = _collect_controller_ids(names, archive)

    if not ctrl_map:
        return None  # no entity client references found

    for name in names:
        if not name.endswith(".json"):
            continue
        fp = name.replace("\\", "/")
        if "animation_controllers" not in fp:
            continue

        try:
            obj = _json_module.loads(
                archive.read(name).decode("utf-8", errors="ignore")
            )
        except Exception:
            continue

        # Detect placeholder: empty dict, empty list, or dict with empty animation_controllers
        if isinstance(obj, list):
            if obj:  # non-empty list — unexpected; skip
                continue
            ac = {}
        elif isinstance(obj, dict):
            ac = obj.get("animation_controllers")
            if obj and (not isinstance(ac, dict) or ac):
                continue
        else:
            continue

        stem = _re_module.sub(
            r"\.animation_controllers\.json$|_animation_controllers\.json$|\.json$",
            "", fp.rsplit("/", 1)[-1],
        )

        ctrl_ids = ctrl_map.get(stem)
        if not ctrl_ids:
            continue

        ac_out = {
            ctrl_id: {"initial_state": "default", "states": {"default": {}}}
            for ctrl_id in sorted(ctrl_ids)
        }

        stub_bytes = _json_module.dumps(
            {"format_version": "1.10.0", "animation_controllers": ac_out},
            indent=2,
        ).encode("utf-8")

        # Key without R/B prefix — must match the filepath seen by fix()
        out_path = fp[2:] if fp.startswith(("R/", "B/")) else fp
        _pending[out_path] = stub_bytes

    return None  # stubs are served via fix(), not via pack-level injection


# ── Per-file API ───────────────────────────────────────────────────────────

def fix(pack_name: str, filepath: str, content: bytes) -> bytes | None:
    """Return populated stub *bytes* when *filepath* matches a pending entry."""
    fp = filepath.replace("\\", "/")
    stub = _pending.get(fp)
    if stub is None:
        return None

    ctrl_count = len(_json_module.loads(stub.decode())["animation_controllers"])
    _logging_module.info(
        "[Fixer] %s: %s (%d controller(s))",
        fp, DESCRIPTION, ctrl_count,
    )
    return stub