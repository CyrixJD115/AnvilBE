"""
Fixes any addon that ships an outdated sounds.json containing sound event
names that were renamed or removed in Bedrock after 1.17, and entity sound
entries that are missing the "key" expression now required for variant sounds.

Errors this silences:
  [Sound][error] - Event name 'X' is not a valid LevelSoundEvent
  [Sound][error] - Expected "key" expression for entity with sound variants
"""

import json
TARGETS = ["*.mcpack", "*.mcaddon"]
DESCRIPTION = "Remove invalid/outdated sound event names from sounds.json"

_INVALID_INDIVIDUAL_EVENTS = {
    "item.bone_meal.use",
    "mob.armor_stand.break",
    "mob.armor_stand.hit",
    "mob.armor_stand.land",
}

_INVALID_ENTITY_EVENTS = {
    "elder_guardian": {"guardian.flop"},
    "fox":            {"sniff", "spit"},
    "ghast":          {"scream"},
    "guardian":       {"guardian.flop"},
    "parrot":         {"imitate.illusion_illager", "imitate.panda"},
    "piglin":         {"jealous"},
}

# Entities whose entry must include a "key" field in modern Bedrock.
# If a pack ships them without "key", drop the entry and let vanilla handle it.
_VARIANT_KEY_REQUIRED = {"cat", "chicken", "cow", "horse", "pig", "wolf"}


def fix(pack_name, filepath, content):
    if filepath != "sounds.json":
        return None
    try:
        data = json.loads(content.decode("utf-8", errors="ignore"))
    except Exception:
        return None

    changed = False

    ind_events = data.get("individual_event_sounds", {}).get("events", {})
    for bad in list(ind_events):
        if bad in _INVALID_INDIVIDUAL_EVENTS:
            del ind_events[bad]
            changed = True

    entity_sounds = data.get("entity_sounds", {})
    # Standard sounds.json nests entity entries under "entities"; some packs omit it
    entities_map = entity_sounds.get("entities") if isinstance(entity_sounds.get("entities"), dict) else entity_sounds

    for entity, bad_events in _INVALID_ENTITY_EVENTS.items():
        ev = entities_map.get(entity, {}).get("events", {})
        for bad in list(ev):
            if bad in bad_events:
                del ev[bad]
                changed = True

    for entity in _VARIANT_KEY_REQUIRED:
        if entity in entities_map and "key" not in entities_map[entity]:
            del entities_map[entity]
            changed = True

    if not changed:
        return None
    return json.dumps(data, indent=3).encode("utf-8")
