"""
Upgrades item behavior files from Bedrock 1.16.x format to 1.20.0.
Bedrock 1.20+ requires format_version 1.20.0 or higher to register custom items:

  [Item][error] - To use item 'sb:foo', use json format version 1.20.0 or higher

Component changes applied:
  minecraft:creative_category  -> minecraft:menu_category
      old: {"parent": "itemGroup.name.tools"}
      new: {"category": "equipment", "group": "itemGroup.name.tools"}
      The category value comes from description.category (lowercased).
  description.category         -> removed (moved into minecraft:menu_category)
  minecraft:food               -> nutrition/saturation_modifier defaults added (required in 1.20.30+)
  minecraft:icon (string)      -> colon namespace normalised to underscore so it matches
                                  item_texture.json keys  ("sb:x" -> "sb_x")
"""

import json as _json

TARGETS = ["*.mcpack", "*.mcaddon"]
DESCRIPTION = "Upgrade old item definitions to 1.20.50 format"

_OLD_VERSIONS = {
    "1.10", "1.10.0", "1.12", "1.12.0", "1.14.0", "1.16.0", "1.16.1",
    "1.16.100", "1.16.200", "1.16.210", "1.16.220",
    "1.17.0", "1.17.10", "1.17.30", "1.17.40",
    "1.18.0", "1.18.10", "1.18.30",
    "1.19.0", "1.19.10", "1.19.20", "1.19.30", "1.19.40", "1.19.50",
    "1.19.60", "1.19.70", "1.19.80",
}

# description.category → minecraft:menu_category.category value
_CATEGORY_MAP = {
    "construction": "construction",
    "equipment":    "equipment",
    "items":        "items",
    "nature":       "nature",
    "commands":     "commands",
    "none":         "none",
}


def fix(pack_name, filepath, content):
    if not filepath.endswith(".json"):
        return None
    fp = filepath.replace("\\", "/")
    if "/items/" not in fp and not fp.startswith("items/"):
        return None
    try:
        data = _json.loads(content.decode("utf-8", errors="ignore"))
    except Exception:
        return None

    item = data.get("minecraft:item")
    if not isinstance(item, dict):
        return None

    fv = str(data.get("format_version", ""))
    if fv not in _OLD_VERSIONS:
        return None

    changed = False
    desc = item.get("description", {})
    comps = item.get("components", {})

    # Pull category from description (old location)
    old_cat = str(desc.pop("category", "items")).lower()
    category = _CATEGORY_MAP.get(old_cat, "items")
    if "category" in (item.get("description") or {}):
        changed = True  # we removed it

    # Convert minecraft:creative_category -> minecraft:menu_category
    if "minecraft:creative_category" in comps:
        old_cc = comps.pop("minecraft:creative_category")
        group = None
        if isinstance(old_cc, dict):
            group = old_cc.get("parent") or old_cc.get("group")
        new_menu = {"category": category}
        if group:
            new_menu["group"] = group
        if "minecraft:menu_category" not in comps:
            comps["minecraft:menu_category"] = new_menu
        changed = True

    # minecraft:food requires nutrition + saturation_modifier in 1.20.30+
    if "minecraft:food" in comps:
        food = comps["minecraft:food"]
        if isinstance(food, dict):
            if "nutrition" not in food:
                food["nutrition"] = 0
            if "saturation_modifier" not in food:
                food["saturation_modifier"] = 0.0
            changed = True

    # minecraft:icon string: normalise colon-namespace to underscore so it matches
    # item_texture.json keys (old format used "sb:x"; texture atlas uses "sb_x")
    if "minecraft:icon" in comps:
        icon = comps["minecraft:icon"]
        if isinstance(icon, str) and ":" in icon:
            comps["minecraft:icon"] = icon.replace(":", "_")
            changed = True

    # minecraft:render_offsets is deprecated in 1.20.50+
    if "minecraft:render_offsets" in comps:
        comps.pop("minecraft:render_offsets")
        changed = True

    # minecraft:use_duration was deprecated; migrate to minecraft:use_modifiers.
    # ONLY apply when the item actually had use_duration OR has minecraft:food —
    # adding use_modifiers to non-food items (swords, tools, armour, etc.) makes
    # them non-functional and can prevent them from registering entirely.
    old_use_dur = comps.pop("minecraft:use_duration", None)
    if old_use_dur is not None:
        changed = True
        if "minecraft:use_modifiers" not in comps:
            dur_val = float(old_use_dur) if isinstance(old_use_dur, (int, float)) else 1.6
            if dur_val != 0:
                comps["minecraft:use_modifiers"] = {"use_duration": dur_val}
    elif "minecraft:food" in comps and "minecraft:use_modifiers" not in comps:
        # Food items require a non-zero use_duration via use_modifiers in 1.20.50+
        comps["minecraft:use_modifiers"] = {"use_duration": 1.6}
        changed = True

    # Always bump format_version for old items even if no other change needed
    changed = True

    data["format_version"] = "1.20.50"
    return _json.dumps(data, indent=2).encode("utf-8")
