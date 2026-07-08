"""
Upgrade legacy item definitions (1.16.x – 1.19.80) to the 1.20.50 schema.

Bedrock 1.20+ refuses to register items with old format versions:
  [Item][error] - To use item 'sb:foo', use json format version 1.20.50+

Changes applied:

  - ``description.category``  →  removed (moved into component)
  - ``minecraft:creative_category`` → ``minecraft:menu_category``
  - ``minecraft:food`` — inject default ``nutrition`` / ``saturation_modifier``
  - ``minecraft:icon`` string with ``:`` → underscore (matches item_texture.json)
  - ``minecraft:render_offsets`` → removed
  - ``minecraft:use_duration`` → ``minecraft:use_modifiers``
  - Food items without ``use_modifiers`` get a default.
  - ``format_version`` is always bumped to ``"1.20.50"``.
"""

from __future__ import annotations

import json as _json_module

TARGETS = ["*.mcpack", "*.mcaddon"]
DESCRIPTION = "Upgrade old item definitions to 1.20.50 format"

_OLD_VERSIONS = frozenset({
    "1.10", "1.10.0", "1.12", "1.12.0", "1.14.0",
    "1.16.0", "1.16.1", "1.16.100", "1.16.200", "1.16.210", "1.16.220",
    "1.17.0", "1.17.10", "1.17.30", "1.17.40",
    "1.18.0", "1.18.10", "1.18.30",
    "1.19.0", "1.19.10", "1.19.20", "1.19.30", "1.19.40", "1.19.50",
    "1.19.60", "1.19.70", "1.19.80",
})

_CATEGORY_MAP = {
    "construction": "construction",
    "equipment": "equipment",
    "items": "items",
    "nature": "nature",
    "commands": "commands",
    "none": "none",
}


# ── Public API ─────────────────────────────────────────────────────────────

def fix(pack_name: str, filepath: str, content: bytes) -> bytes | None:
    """Return upgraded *bytes*, or ``None`` when no change is needed."""
    if not filepath.endswith(".json"):
        return None

    normalised = filepath.replace("\\", "/")
    if "/items/" not in normalised and not normalised.startswith("items/"):
        return None

    try:
        data = _json_module.loads(content.decode("utf-8", errors="ignore"))
    except Exception:
        return None

    item = data.get("minecraft:item")
    if not isinstance(item, dict):
        return None

    current_fmt = str(data.get("format_version", ""))
    if current_fmt not in _OLD_VERSIONS:
        return None

    changed = False
    desc = item.get("description", {})
    comps = item.get("components", {})

    # ── Pull (and remove) category from description ────────────────────
    old_cat = str(desc.pop("category", "items")).lower()
    category = _CATEGORY_MAP.get(old_cat, "items")
    if "category" in (item.get("description") or {}):
        changed = True

    # ── minecraft:creative_category → minecraft:menu_category ──────────
    if "minecraft:creative_category" in comps:
        old = comps.pop("minecraft:creative_category")
        group = old.get("parent") or old.get("group") if isinstance(old, dict) else None
        menu = {"category": category}
        if group:
            menu["group"] = group
        if "minecraft:menu_category" not in comps:
            comps["minecraft:menu_category"] = menu
        changed = True

    # ─── minecraft:food — ensure nutrition + saturation_modifier ───────
    if "minecraft:food" in comps:
        food = comps["minecraft:food"]
        if isinstance(food, dict):
            if "nutrition" not in food:
                food["nutrition"] = 0
                changed = True
            if "saturation_modifier" not in food:
                food["saturation_modifier"] = 0.0
                changed = True

    # ── minecraft:icon string with colon → underscore ─────────────────
    if "minecraft:icon" in comps:
        icon = comps["minecraft:icon"]
        if isinstance(icon, str) and ":" in icon:
            comps["minecraft:icon"] = icon.replace(":", "_")
            changed = True

    # ── minecraft:render_offsets → removed ─────────────────────────────
    if "minecraft:render_offsets" in comps:
        comps.pop("minecraft:render_offsets")
        changed = True

    # ── minecraft:use_duration → minecraft:use_modifiers ───────────────
    old_duration = comps.pop("minecraft:use_duration", None)
    if old_duration is not None:
        changed = True
        if "minecraft:use_modifiers" not in comps:
            duration = float(old_duration) if isinstance(old_duration, (int, float)) else 1.6
            if duration != 0:
                comps["minecraft:use_modifiers"] = {"use_duration": duration}
    elif "minecraft:food" in comps and "minecraft:use_modifiers" not in comps:
        comps["minecraft:use_modifiers"] = {"use_duration": 1.6}
        changed = True

    # ── Always bump format_version ───────────────────────────────────
    changed = True
    data["format_version"] = "1.20.50"

    return _json_module.dumps(data, indent=2).encode("utf-8")