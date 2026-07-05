"""
Updates block behavior files that were written for Bedrock 1.16.x-1.19.70 to use
the modern 1.20.10 component schema. Bedrock 1.20+ rejects the old components, which
prevents the block from registering and causes cascading errors:

  [Texture][warning] - The block named X used in a "blocks.json" file does not
                       exist in the registry
  [Recipe][error]    - The Item: X is missing or invalid, can't make the recipe

Component mappings applied (only when the old key is present):
  minecraft:block_light_absorption  -> minecraft:light_dampening  (int 0-15)
  minecraft:block_light_emission    -> minecraft:light_emission    (float 0.0-1.0)
  minecraft:destroy_time            -> minecraft:destructible_by_mining
  minecraft:explosion_resistance    -> minecraft:destructible_by_explosion
  minecraft:creative_category       -> removed (category lives in description)
  minecraft:entity_collision        -> minecraft:collision_box
  minecraft:pick_collision          -> minecraft:selection_box
  minecraft:on_placed / on_player_placing / on_step_on / on_step_off /
  on_player_destroyed / on_fall_on / ticking / random_ticking
                                    -> REMOVED (require Holiday Creator Features
                                       experimental toggle; blocks fail with
                                       "Unexpected version" without it)
  description.category              -> removed (invalid in 1.20.10)

Structural renames:
  description.properties  -> description.states
  query.block_property(   -> query.block_state(  (permutation conditions)
  set_block_property      -> set_block_state     (block event actions)
  events section          -> REMOVED (no longer needed without event triggers)
"""

import json as _json
import re as _re

TARGETS = ["*.mcpack", "*.mcaddon"]
DESCRIPTION = "Upgrade old block definitions to 1.20.10 (strip experimental event triggers)"

# Event trigger components that require the 'Holiday Creator Features' experimental
# toggle.  Without it the entire block fails with 'Unexpected version for the loaded
# data'.  Removing them lets the block register so items/recipes work even though the
# triggered behaviours (golem spawning, rotation snapping, etc.) are lost.
_EVENT_TRIGGER_COMPONENTS = {
    "minecraft:on_player_placing",
    "minecraft:on_placed",
    "minecraft:on_player_destroyed",
    "minecraft:on_step_on",
    "minecraft:on_step_off",
    "minecraft:on_fall_on",
    "minecraft:ticking",
    "minecraft:random_ticking",
}

_OLD_VERSIONS = {
    "1.16.0", "1.16.1", "1.16.100", "1.16.200", "1.16.210", "1.16.220",
    "1.17.0", "1.17.10", "1.17.30", "1.17.40",
    "1.18.0", "1.18.10", "1.18.30",
    "1.19.0", "1.19.10", "1.19.20", "1.19.30", "1.19.40", "1.19.50",
    "1.19.60", "1.19.70",
}


def _migrate_components(comps):
    """Apply in-place component renames. Returns True if anything changed."""
    if not isinstance(comps, dict):
        return False
    changed = False

    # minecraft:block_light_absorption -> minecraft:light_dampening
    if "minecraft:block_light_absorption" in comps:
        val = comps.pop("minecraft:block_light_absorption")
        if "minecraft:light_dampening" not in comps:
            absorption = val if isinstance(val, (int, float)) else 15
            comps["minecraft:light_dampening"] = int(max(0, min(15, absorption)))
        changed = True

    # minecraft:block_light_emission -> minecraft:light_emission
    if "minecraft:block_light_emission" in comps:
        val = comps.pop("minecraft:block_light_emission")
        if "minecraft:light_emission" not in comps:
            comps["minecraft:light_emission"] = float(val) if isinstance(val, (int, float)) else 0.0
        changed = True

    # minecraft:destroy_time -> minecraft:destructible_by_mining
    if "minecraft:destroy_time" in comps:
        val = comps.pop("minecraft:destroy_time")
        if "minecraft:destructible_by_mining" not in comps:
            comps["minecraft:destructible_by_mining"] = {
                "seconds_to_destroy": float(val) if isinstance(val, (int, float)) else 0.0
            }
        changed = True

    # minecraft:explosion_resistance -> minecraft:destructible_by_explosion
    if "minecraft:explosion_resistance" in comps:
        val = comps.pop("minecraft:explosion_resistance")
        if "minecraft:destructible_by_explosion" not in comps:
            comps["minecraft:destructible_by_explosion"] = {
                "explosion_resistance": float(val) if isinstance(val, (int, float)) else 0.0
            }
        changed = True

    # minecraft:creative_category is not a valid component; drop it
    if "minecraft:creative_category" in comps:
        comps.pop("minecraft:creative_category")
        changed = True

    # minecraft:rotation (array) -> minecraft:transformation {"rotation": [...]}
    # minecraft:rotation is not valid in 1.20.10 stable blocks; it causes
    # "child 'minecraft:rotation' not valid here" which then triggers
    # "Unexpected version for the loaded data" for the entire block.
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
        changed = True

    # minecraft:flammable old format {flame_odds, burn_odds} -> new stable format
    if "minecraft:flammable" in comps:
        fl = comps["minecraft:flammable"]
        if isinstance(fl, dict) and ("flame_odds" in fl or "burn_odds" in fl):
            comps["minecraft:flammable"] = {
                "catch_chance_modifier": fl.get("flame_odds", 5),
                "destroy_chance_modifier": fl.get("burn_odds", 20),
            }
            changed = True

    # minecraft:placement_filter block_filter: old string items -> object items
    if "minecraft:placement_filter" in comps:
        pf = comps["minecraft:placement_filter"]
        if isinstance(pf, dict):
            for _cond in pf.get("conditions", []):
                if not isinstance(_cond, dict):
                    continue
                _bf = _cond.get("block_filter", [])
                if not isinstance(_bf, list):
                    continue
                _new_bf = []
                _bf_changed = False
                for _entry in _bf:
                    if isinstance(_entry, str):
                        _name = _entry if ":" in _entry else "minecraft:" + _entry
                        _new_bf.append({"name": _name})
                        _bf_changed = True
                    else:
                        _new_bf.append(_entry)
                if _bf_changed:
                    _cond["block_filter"] = _new_bf
                    changed = True

    # minecraft:map_color is not a valid component in 1.20.10 stable blocks
    if "minecraft:map_color" in comps:
        comps.pop("minecraft:map_color")
        changed = True

    # Strip event trigger components that need Holiday Creator Features
    for _etc in _EVENT_TRIGGER_COMPONENTS:
        if _etc in comps:
            comps.pop(_etc)
            changed = True

    # minecraft:entity_collision -> minecraft:collision_box
    if "minecraft:entity_collision" in comps:
        val = comps.pop("minecraft:entity_collision")
        if "minecraft:collision_box" not in comps:
            comps["minecraft:collision_box"] = val
        changed = True

    # minecraft:pick_collision -> minecraft:selection_box
    if "minecraft:pick_collision" in comps:
        val = comps.pop("minecraft:pick_collision")
        if "minecraft:selection_box" not in comps:
            comps["minecraft:selection_box"] = val
        changed = True

    return changed


def fix(pack_name, filepath, content):
    if not filepath.endswith(".json"):
        return None
    fp = filepath.replace("\\", "/")
    if "/blocks/" not in fp and not fp.startswith("blocks/"):
        return None
    try:
        data = _json.loads(content.decode("utf-8", errors="ignore"))
    except Exception:
        return None

    block = data.get("minecraft:block")
    if not isinstance(block, dict):
        return None

    fv = str(data.get("format_version", ""))
    if fv not in _OLD_VERSIONS:
        return None

    changed = False

    # Remove description.category — invalid field in 1.20.10 blocks
    desc = block.get("description", {})
    if isinstance(desc, dict):
        if "category" in desc:
            desc.pop("category")
            changed = True
        # Strip the block-state declaration — event triggers that would drive
        # the state are already removed, so the state is frozen at default.
        # The state + permutation schema is the last known cause of
        # "Unexpected version" in 1.20.10 stable blocks.
        for _sf in ("states", "properties"):
            if _sf in desc:
                desc.pop(_sf)
                changed = True

    # Strip permutations — they only served to apply rotation via the now-
    # removed block state, so they are both non-functional and potentially
    # schema-invalid in the user's current Bedrock version.
    if "permutations" in block:
        block.pop("permutations")
        changed = True

    # Migrate top-level components
    if _migrate_components(block.get("components", {})):
        changed = True

    # Remove the events section — event triggers have been stripped so events
    # are unreachable and some event content uses APIs unavailable in 1.20.10
    if "events" in block:
        block.pop("events")
        changed = True

    if not changed:
        return None

    data["format_version"] = "1.20.10"
    return _json.dumps(data, indent=2).encode("utf-8")
