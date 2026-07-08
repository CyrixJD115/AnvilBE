"""
Migrate legacy block definitions (1.16.x – 1.19.70) to the modern 1.20.10
component schema.

Bedrock 1.20+ rejects several old-style components, preventing the block from
registering and causing cascading failures:
  [Texture][warning] - The block named X used in "blocks.json" does not exist
  [Recipe][error]  - The Item: X is missing or invalid, can't make the recipe

Component mappings applied (only when the old key is present):

  minecraft:block_light_absorption   →  minecraft:light_dampening
  minecraft:block_light_emission       →  minecraft:light_emission
  minecraft:destroy_time           →  minecraft:destructible_by_mining
  minecraft:explosion_resistance     →  minecraft:destructible_by_explosion
  minecraft:creative_category        →  removed
  minecraft:entity_collision         →  minecraft:entity_collision
  minecraft:pick_collision          →  minecraft:selection_box
  minecraft:rotation                 →  minecraft:transformation  {"rotation": [...]}
  minecraft:flammable (old format)   →  minecraft:flammable (new format)
  minecraft:placement_filter         →  (string → object items)
  minecraft:map_color                →  removed
  Event-trigger components          →  removed (needs Holiday Creator Features)

Structural changes:
  description.properties  →  removed
  description.states   →  removed
  description.category  →  removed
  permutations         →  removed (depend on removed state)
  events               →  removed (triggers removed)
"""

from __future__ import annotations

import json as _json_module
import re as _re_module

TARGETS = ["*.mcpack", "*.mcaddon"]
DESCRIPTION = "Upgrade old block definitions to 1.20.10 (strip experimental event triggers)"

_OLD_VERSIONS = frozenset({
    "1.16.0", "1.16.1", "1.16.100", "1.16.200", "1.16.210", "1.16.220",
    "1.17.0", "1.17.10", "1.17.30", "1.17.40",
    "1.18.0", "1.18.10", "1.18.30",
    "1.19.0", "1.19.10", "1.19.20", "1.19.30", "1.19.40", "1.19.50",
    "1.19.60", "1.19.70",
})

_EVENT_TRIGGER_KEYS = frozenset({
    "minecraft:on_player_placing",
    "minecraft:on_placed",
    "minecraft:on_player_destroyed",
    "minecraft:on_step_on",
    "minecraft:on_step_off",
    "minecraft:on_fall_on",
    "minecraft:ticking",
    "minecraft:random_ticking",
})


# ── Component migration ────────────────────────────────────────────────────

def _migrate_components(comps: dict) -> bool:
    """Apply in-place renames; return ``True`` when anything changed."""
    if not isinstance(comps, dict):
        return False

    dirty = False

    # minecraft:block_light_absorption → minecraft:light_dampening
    if "minecraft:block_light_absorption" in comps:
        val = comps.pop("minecraft:block_light_absorption")
        if "minecraft:light_dampening" not in comps:
            comps["minecraft:light_dampening"] = int(max(0, min(15, val if isinstance(val, (int, float)) else 15)))
        dirty = True

    # minecraft:block_light_emission → minecraft:light_emission
    if "minecraft:block_light_emission" in comps:
        val = comps.pop("minecraft:block_light_emission")
        if "minecraft:light_emission" not in comps:
            comps["minecraft:light_emission"] = float(val) if isinstance(val, (int, float)) else 0.0
        dirty = True

    # minecraft:destroy_time → minecraft:destructible_by_mining
    if "minecraft:destroy_time" in comps:
        val = comps.pop("minecraft:destroy_time")
        if "minecraft:destructible_by_mining" not in comps:
            comps["minecraft:destructible_by_mining"] = {
                "seconds_to_destroy": float(val) if isinstance(val, (int, float)) else 0.0
            }
        dirty = True

    # minecraft:explosion_resistance → minecraft:destructible_by_explosion
    if "minecraft:explosion_resistance" in comps:
        val = comps.pop("minecraft:explosion_resistance")
        if "minecraft:destructible_by_explosion" not in comps:
            comps["minecraft:destructible_by_explosion"] = {
                "explosion_resistance": float(val) if isinstance(val, (int, float)) else 0.0
            }
        dirty = True

    # minecraft:creative_category → removed
    if "minecraft:creative_category" in comps:
        comps.pop("minecraft:creative_category")
        dirty = True

    # minecraft:rotation → minecraft:transformation
    if "minecraft:rotation" in comps:
        rot = comps.pop("minecraft:rotation")
        if "minecraft:transformation" not in comps:
            if isinstance(rot, list):
                rotation = rot
            elif isinstance(rot, dict):
                rotation = [rot.get("x", 0), rot.get("y", 0), rot.get("z", 0)]
            else:
                rotation = [0, 0, 0]
            comps["minecraft:transformation"] = {"rotation": rotation}
        dirty = True

    # minecraft:flammable (old format {flame_odds, burn_odds})
    if "minecraft:flammable" in comps:
        fl = comps["minecraft:flammable"]
        if isinstance(fl, dict) and ("flame_odds" in fl or "burn_odds" in fl):
            comps["minecraft:flammable"] = {
                "catch_chance_modifier": fl.get("flame_odds", 5),
                "destroy_chance_modifier": fl.get("burn_odds", 20),
            }
            dirty = True

    # minecraft:placement_filter — string items → object items
    if "minecraft:placement_filter" in comps:
        pf = comps["minecraft:placement_filter"]
        if isinstance(pf, dict):
            for condition in pf.get("conditions", []):
                if not isinstance(condition, dict):
                    continue
                raw_filter = condition.get("block_filter", [])
                if not isinstance(raw_filter, list):
                    continue
                new_filter: list[dict] = []
                filter_dirty = False
                for entry in raw_filter:
                    if isinstance(entry, str):
                        name = entry if ":" in entry else "minecraft:" + entry
                        new_filter.append({"name": name})
                        filter_dirty = True
                    else:
                        new_filter.append(entry)
                if filter_dirty:
                    condition["block_filter"] = new_filter
                    dirty = True

    # minecraft:map_color → removed
    if "minecraft:map_color" in comps:
        comps.pop("minecraft:map_color")
        dirty = True

    # Strip event-trigger components
    for trigger in _EVENT_TRIGGER_KEYS:
        if trigger in comps:
            comps.pop(trigger)
            dirty = True

    # minecraft:entity_collision → minecraft:collision_box
    if "minecraft:entity_collision" in comps:
        val = comps.pop("minecraft:entity_collision")
        if "minecraft:collision_box" not in comps:
            comps["minecraft:collision_box"] = val
        dirty = True

    # minecraft:pick_collision → minecraft:selection_box
    if "minecraft:pick_collision" in comps:
        val = comps.pop("minecraft:pick_collision")
        if "minecraft:selection_box" not in comps:
            comps["minecraft:selection_box"] = val
        dirty = True

    return dirty


# ── Public API ───────────────────────────────────────────────────────────────

def fix(pack_name: str, filepath: str, content: bytes) -> bytes | None:
    """Return modernised *bytes*, or ``None`` when no change is needed."""
    if not filepath.endswith(".json"):
        return None

    normalised = filepath.replace("\\", "/")
    if "/blocks/" not in normalised and not normalised.startswith("blocks/"):
        return None

    try:
        data = _json_module.loads(content.decode("utf-8", errors="ignore"))
    except Exception:
        return None

    block = data.get("minecraft:block")
    if not isinstance(block, dict):
        return None

    current_fmt = str(data.get("format_version", ""))
    if current_fmt not in _OLD_VERSIONS:
        return None

    changed = False

    # ── Clean up description ───────────────────────────────────────────
    desc = block.get("description", {})
    if isinstance(desc, dict):
        if "category" in desc:
            desc.pop("category")
            changed = True
        for sf in ("states", "properties"):
            if sf in desc:
                desc.pop(sf)
                changed = True

    # ── Drop permutations (depend on removed states) ───────────────────
    if "permutations" in block:
        block.pop("permutations")
        changed = True

    # ── Migrate components ────────────────────────────────────────────
    if _migrate_components(block.get("components", {})):
        changed = True

    # ── Remove unreachable events section ──────────────────────────────
    if "events" in block:
        block.pop("events")
        changed = True

    if not changed:
        return None

    data["format_version"] = "1.20.10"
    return _json_module.dumps(data, indent=2).encode("utf-8")