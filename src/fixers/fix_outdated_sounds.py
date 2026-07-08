"""
Strip outdated or renamed sound events from ``sounds.json``.

Bedrock errors silenced:
  [Sound][error] - Event name 'X' is not a valid LevelSoundEvent
  [Sound][error] - Expected "key" expression for entity with sound variants

Two passes:

  1. Remove known-invalid individual sound events.
  2. Remove known-invalid entity-specific sound events.
  3. Drop entity entries that are missing a ``"key"`` field (required in modern
     Bedrock for variant-sound entities).
"""

from __future__ import annotations

import json as _json_module

TARGETS = ["*.mcpack", "*.mcaddon"]
DESCRIPTION = "Remove invalid / outdated sound event names from sounds.json"

_INVALID_INDIVIDUAL_EVENTS = frozenset({
    "item.bone_meal.use",
    "mob.armor_stand.break",
    "mob.armor_stand.hit",
    "mob.armor_stand.land",
})

_INVALID_ENTITY_EVENTS: dict[str, frozenset[str]] = {
    "elder_guardian": frozenset({"guardian.flop"}),
    "fox": frozenset({"sniff", "spit"}),
    "ghast":         frozenset({"scream"}),
    "guardian":      frozenset({"guardian.flop"}),
    "parrot":        frozenset({"imitate.illusion_illager", "imitate.panda"}),
    "piglin":        frozenset({"jealous"}),
}

_ENTITIES_REQUIRING_KEY = frozenset({"cat", "chicken", "cow", "horse", "pig", "wolf"})


# ── Public API ─────────────────────────────────────────────────────────────

def fix(pack_name: str, filepath: str, content: bytes) -> bytes | None:
    """Return sanitised *bytes*, or ``None`` when no change is needed."""
    if filepath != "sounds.json":
        return None

    try:
        data = _json_module.loads(content.decode("utf-8", errors="ignore"))
    except Exception:
        return None

    changed = False

    # ── 1. Individual event sounds ─────────────────────────────────────
    ind_events = data.get("individual_event_sounds", {}).get("events", {})
    for bad in list(ind_events):
        if bad in _INVALID_INDIVIDUAL_EVENTS:
            del ind_events[bad]
            changed = True

    # ── 2. Entity sounds — locate the entities dict ────────────────────
    entity_sounds = data.get("entity_sounds", {})
    # Standard layout nests entities under ``"entities"``; some packs skip that.
    entities = (
        entity_sounds["entities"]
        if isinstance(entity_sounds.get("entities"), dict)
        else entity_sounds
    )

    # ── 2a. Remove invalid per-entity events ────────────────────────────
    for entity, bad_set in _INVALID_ENTITY_EVENTS.items():
        ev = entities.get(entity, {}).get("events", {})
        for bad in list(ev):
            if bad in bad_set:
                del ev[bad]
                changed = True

    # ── 2b. Drop entities that lack the required ``key`` field ─────────
    for entity in _ENTITIES_REQUIRING_KEY:
        if entity in entities and "key" not in entities[entity]:
            del entities[entity]
            changed = True

    if not changed:
        return None

    return _json_module.dumps(data, indent=3).encode("utf-8")