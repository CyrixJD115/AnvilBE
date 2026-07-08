"""
Universal Compatibility Patcher for AutoBE

Detects and repairs common merge-time compatibility issues across all addon
types.  Restores missing critical sections, merges animations, animation
controllers, and re-injects ``format_version`` when it has been stripped.
"""

from __future__ import annotations

import logging as _logging_module
from typing import Any

_logger = _logging_module.getLogger(__name__)


# ── Critical section sets ──────────────────────────────────────────────────

_CRITICAL_ENTITY_SECTIONS = frozenset({
    "materials", "textures", "geometry", "render_controllers",
})

_MERGE_WITH_PRESERVE = frozenset({
    "materials", "textures", "geometry",
})


# ── UniversalCompatibilityPatcher ─────────────────────────────────────────

class UniversalCompatibilityPatcher:
    """Patch merged JSON files to restore sections lost during conflict resolution."""

    def __init__(self) -> None:
        self.patches_applied: list[dict[str, Any]] = []

    # ── Main entry point ───────────────────────────────────────────────

    def patch_merged_file(
        self,
        merged: dict[str, Any],
        sources: list[dict[str, Any]],
        file_path: str,
    ) -> dict[str, Any]:
        """Run all applicable patches against *merged* using *sources* for context."""
        if not sources:
            return merged

        ftype = self._classify(file_path, merged)

        if ftype == "entity":
            merged = self._patch_entity(merged, sources, file_path)
        elif ftype == "client_entity":
            merged = self._patch_client_entity(merged, sources, file_path)
        elif ftype == "animation":
            merged = self._patch_animation(merged, sources, file_path)
        elif ftype == "animation_controller":
            merged = self._patch_anim_ctrl(merged, sources, file_path)

        merged = self._patch_universal(merged, sources, file_path)
        return merged

    # ── File-type classifier ─────────────────────────────────────────

    @staticmethod
    def _classify(file_path: str, data: dict[str, Any]) -> str:
        """Return one of ``entity``, ``client_entity``, ``animation``, ``animation_controller``, or ``generic``."""
        lower = file_path.lower()
        if "entity" in lower:
            if "client_entity" in str(data) or "minecraft:client_entity" in str(data):
                return "client_entity"
            return "entity"
        if "animation" in lower:
            if "controller" in lower or "animation_controllers" in lower:
                return "animation_controller"
            return "animation"
        return "generic"

    # ── Entity patch (BP) ───────────────────────────────────────────

    @staticmethod
    def _patch_entity(
        merged: dict[str, Any],
        sources: list[dict[str, Any]],
        file_path: str,
    ) -> dict[str, Any]:
        """BP entities do not carry RP-side sections; this is a no-op."""
        return merged

    # ── Client entity patch (RP) ────────────────────────────────────

    def _patch_client_entity(
        self,
        merged: dict[str, Any],
        sources: list[dict[str, Any]],
        file_path: str,
    ) -> dict[str, Any]:
        """Restore missing critical sections in ``minecraft:client_entity``."""
        if "minecraft:client_entity" not in merged:
            return merged

        description = merged["minecraft:client_entity"].get("description", {})
        missing = _CRITICAL_ENTITY_SECTIONS - set(description.keys())

        if missing:
            _logger.debug("Client entity file missing sections %s in %s", missing, file_path)
            for src in sources:
                if "minecraft:client_entity" not in src:
                    continue
                src_desc = src["minecraft:client_entity"].get("description", {})
                for section in missing:
                    if section not in src_desc:
                        continue
                    if section not in description:
                        description[section] = src_desc[section]
                        self._record(file_path, "restored_section", section=section)
                        _logger.info("Restored %s section in %s", section, file_path)
                    elif isinstance(description[section], dict) and isinstance(src_desc[section], dict):
                        description[section] = UniversalCompatibilityPatcher._deep_merge(description[section], src_desc[section])
                        self._record(file_path, "merged_section", section=section)

        # Ensure default texture is preserved
        if "textures" in description:
            for src in sources:
                if "minecraft:client_entity" not in src:
                    continue
                src_desc = src["minecraft:client_entity"].get("description", {})
                s_textures = src_desc.get("textures", {})
                if "default" in s_textures and "default" not in description["textures"]:
                    description["textures"]["default"] = s_textures["default"]
                    self._record(file_path, "restored_texture", texture="default", value=s_textures["default"])
                    _logger.info("Restored default texture in %s", file_path)

        merged["minecraft:client_entity"]["description"] = description
        return merged

    # ── Animation patch ──────────────────────────────────────────────

    @staticmethod
    def _patch_animation(
        merged: dict[str, Any],
        sources: list[dict[str, Any]],
        file_path: str,
    ) -> dict[str, Any]:
        """Re-inject any animations that were lost during the merge."""
        if "format_version" not in merged or "animations" not in merged:
            return merged

        merged_anims = merged["animations"]
        for src in sources:
            if "animations" not in src:
                continue
            for name, data in src["animations"].items():
                if name not in merged_anims:
                    merged_anims[name] = data

        merged["animations"] = merged_anims
        return merged

    # ── Animation controller patch ─────────────────────────────────

    @staticmethod
    def _patch_anim_ctrl(
        merged: dict[str, Any],
        sources: list[dict[str, Any]],
        file_path: str,
    ) -> dict[str, Any]:
        """Re-inject controllers that were lost during merge."""
        if "format_version" not in merged or "animation_controllers" not in merged:
            return merged

        ctrls = merged["animation_controllers"]
        for src in sources:
            if "animation_controllers" not in src:
                continue
            for name, data in src["animation_controllers"].items():
                if name not in ctrls:
                    ctrls[name] = data

        merged["animation_controllers"] = ctrls
        return merged

    # ── Universal patches ───────────────────────────────────────────

    @staticmethod
    def _patch_universal(
        merged: dict[str, Any],
        sources: list[dict[str, Any]],
        file_path: str,
    ) -> dict[str, Any]:
        """Ensure ``format_version`` is present, restoring from first source if missing."""
        if "format_version" in merged:
            return merged

        for src in sources:
            if "format_version" in src:
                merged["format_version"] = src["format_version"]
                break
        return merged

    # ── Helpers ─────────────────────────────────────────────────────

    @staticmethod
    def _deep_merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
        """Recursively merge *overlay* into *base*."""
        result = base.copy()
        for key, value in overlay.items():
            if key not in result:
                result[key] = value
            elif isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = UniversalCompatibilityPatcher._deep_merge(result[key], value)
            elif isinstance(result[key], list) and isinstance(value, list):
                result[key] = result[key] + [item for item in value if item not in result[key]]
            else:
                result[key] = value
        return result

    def _record(self, file_path: str, patch_type: str, **extra: Any) -> None:
        """Append an entry to the patch history."""
        self.patches_applied.append({
            "file": file_path,
            "type": patch_type,
            **extra,
        })

    # ── Reporting ───────────────────────────────────────────────────

    def get_patch_report(self) -> list[dict[str, Any]]:
        """Return the list of all patches that have been applied."""
        return self.patches_applied

    def clear_patches(self) -> None:
        """Reset patch history."""
        self.patches_applied = []