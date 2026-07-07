"""
Universal JSON merger for Minecraft Bedrock Edition pack merging.
Intelligently merges JSON files based on their structure and context,
detecting file types and applying appropriate merge strategies.

Merge strategies:
- format_version: Keep highest version
- scripts/initialize: Concatenate with variable conflict detection
- scripts/pre_animation/animate: Concatenate with duplicate removal
- animations: Smart merge with compatibility checking
- materials/textures/geometry: Merge dictionaries
- render_controllers: First-wins per controller ID
- variables: Merge with namespace conflict detection
- Lists: Concatenate with duplicate detection
- Dicts: Recursive merge
"""
import re
import logging
class UniversalJsonMerger:
    """
    Intelligent JSON merger with context-aware strategies based on file structure.
    """

    def __init__(self):
        # Keys that should use first-wins strategy (merge by key, keep first definition)
        self.first_wins_keys = {
            'animations', 'animation_controllers', 'render_controllers',
            'materials', 'textures', 'sounds', 'particle_effects'
        }

        # Keys that should concatenate arrays
        self.concatenate_keys = {
            'initialize', 'pre_animation', 'animate', 'scripts'
        }

        # Keys that should keep highest version (numeric comparison)
        self.version_keys = {'format_version', 'min_engine_version'}

        # Keys that are dictionaries but should be merged by key
        self.dict_merge_keys = {
            'variables', 'description'
        }

        # Track conflicts for reporting
        self.conflicts = []
        self.warnings = []
        self._universal_patcher = None

    def set_universal_patcher(self, patcher):
        """Set the universal compatibility patcher for post-merge patch application."""
        self._universal_patcher = patcher

    def merge_json_list(self, json_list, file_path=None):
        """
        Merge a list of JSON objects into a single merged object.
        Uses context-aware strategies based on the JSON structure.
        """
        if not json_list:
            return {}

        self.conflicts = []
        self.warnings = []

        if json_list:
            file_type = self._detect_file_type(json_list[0], file_path)
        else:
            file_type = 'generic'

        merged = json_list[0].copy()

        for json_obj in json_list[1:]:
            try:
                merged = self._merge_objects(merged, json_obj, file_type, path='')
            except Exception as e:
                self.warnings.append(f"Smart merge failed for {file_path}, using fallback: {e}")
                merged = self._fallback_merge(merged, json_obj)

        if self.conflicts:
            logging.warning(f"Merge conflicts detected in {file_path}: {len(self.conflicts)} conflict(s)")
            for conflict in self.conflicts:
                logging.warning(f"  - {conflict}")
        if self.warnings:
            logging.warning(f"Merge warnings in {file_path}: {len(self.warnings)} warning(s)")
            for warning in self.warnings:
                logging.warning(f"  - {warning}")

        # Apply universal compatibility patches if available
        if self._universal_patcher:
            merged = self._universal_patcher.patch_merged_file(merged, json_list, file_path)
            patches = self._universal_patcher.get_patch_report()
            if patches:
                logging.info(f"Applied {len(patches)} universal compatibility patch(es) to {file_path}")

        return merged

    def _detect_file_type(self, json_obj, file_path):
        """Detect the type of JSON file based on structure and path."""
        if file_path:
            fpath = file_path.lower()
            if 'entity' in fpath and fpath.endswith('.json'):
                if 'client_entity' in fpath or 'minecraft:client_entity' in str(json_obj):
                    return 'client_entity'
                elif 'minecraft:entity' in str(json_obj):
                    return 'entity'
            elif 'item' in fpath:
                return 'item'
            elif 'block' in fpath:
                return 'block'

        if 'minecraft:client_entity' in json_obj:
            return 'client_entity'
        elif 'minecraft:entity' in json_obj:
            return 'entity'
        elif 'minecraft:item' in json_obj:
            return 'item'
        elif 'minecraft:block' in json_obj:
            return 'block'

        return 'generic'

    def _merge_objects(self, base, overlay, file_type, path):
        """Recursively merge *overlay* into *base* with context-aware strategies."""
        for key, value in overlay.items():
            current_path = f"{path}.{key}" if path else key

            if key not in base:
                base[key] = value
            elif isinstance(base[key], dict) and isinstance(value, dict):
                if key in self.first_wins_keys:
                    for entry_id, entry_data in value.items():
                        if entry_id not in base[key]:
                            base[key][entry_id] = entry_data
                        else:
                            if self._are_entries_compatible(base[key][entry_id], entry_data, key):
                                base[key][entry_id] = self._merge_objects(
                                    base[key][entry_id], entry_data, file_type, current_path)
                            else:
                                self.conflicts.append(
                                    f"Incompatible {key} entry '{entry_id}' at {current_path}")
                elif key in self.dict_merge_keys:
                    if key == 'variables':
                        base[key] = self._merge_variables(base[key], value, current_path)
                    else:
                        base[key] = self._merge_objects(base[key], value, file_type, current_path)
                else:
                    base[key] = self._merge_objects(base[key], value, file_type, current_path)
            elif isinstance(base[key], list) and isinstance(value, list):
                if key in self.concatenate_keys or 'scripts' in current_path:
                    if key == 'initialize' or 'initialize' in current_path:
                        base[key] = self._concatenate_with_variable_check(
                            base[key], value, current_path)
                    else:
                        base[key] = self._concatenate_unique(base[key], value, current_path)
                else:
                    base[key] = value
            elif key in self.version_keys:
                base[key] = self._compare_versions(base[key], value)
            else:
                base[key] = value

        return base

    def _are_entries_compatible(self, entry1, entry2, key_type):
        """Check if two entries (animations, controllers, etc.) are compatible for merging."""
        if type(entry1) != type(entry2):
            return False

        if isinstance(entry1, dict) and isinstance(entry2, dict):
            keys1 = set(entry1.keys())
            keys2 = set(entry2.keys())
            if abs(len(keys1) - len(keys2)) > 3:
                return False

            critical_keys = {'loops', 'blend_expression', 'anim_time_update', 'transition_duration'}
            for ck in critical_keys:
                if ck in keys1 and ck in keys2:
                    if entry1[ck] != entry2[ck]:
                        return False

        return True

    def _merge_variables(self, base_vars, overlay_vars, path):
        """Merge variable dictionaries with conflict detection."""
        for var_name, var_value in overlay_vars.items():
            if var_name not in base_vars:
                base_vars[var_name] = var_value
            elif base_vars[var_name] != var_value:
                self.warnings.append(
                    f"Variable '{var_name}' redefined with different value at {path}")
                base_vars[var_name] = var_value
        return base_vars

    def _concatenate_with_variable_check(self, base_list, overlay_list, path):
        """Concatenate script arrays with variable redefinition detection."""
        base_vars = self._extract_variables(base_list)
        overlay_vars = self._extract_variables(overlay_list)
        for var_name in overlay_vars:
            if var_name in base_vars and base_vars[var_name] != overlay_vars[var_name]:
                self.warnings.append(f"Variable '{var_name}' redefined in scripts at {path}")
        return self._concatenate_unique(base_list, overlay_list, path)

    def _extract_variables(self, script_list):
        """Extract variable declarations from a script array."""
        variables = {}
        for item in script_list:
            if isinstance(item, str):
                match = re.search(r'(?:variable|v)\.(\w+)\s*=\s*(.+)', item)
                if match:
                    variables[match.group(1)] = match.group(2).strip()
        return variables

    def _concatenate_unique(self, base_list, overlay_list, path):
        """Concatenate two lists while avoiding duplicates (by string representation)."""
        existing = set(str(item) for item in base_list)
        result = list(base_list)
        for item in overlay_list:
            if str(item) not in existing:
                result.append(item)
                existing.add(str(item))
        return result

    def _fallback_merge(self, base, overlay):
        """Fallback merge for non-standard structures; last-wins for values, concatenate for lists."""
        try:
            for key, value in overlay.items():
                if key not in base:
                    base[key] = value
                elif isinstance(base[key], dict) and isinstance(value, dict):
                    base[key] = self._fallback_merge(base[key], value)
                elif isinstance(base[key], list) and isinstance(value, list):
                    base[key] = base[key] + value
                else:
                    base[key] = value
        except Exception as e:
            self.warnings.append(f"Fallback merge error: {e}")
        return base

    def _compare_versions(self, v1, v2):
        """Compare two version values and return the highest."""
        try:
            if isinstance(v1, list) and isinstance(v2, list):
                for a, b in zip(v1, v2):
                    if a > b:
                        return v1
                    elif b > a:
                        return v2
                return v1
            elif isinstance(v1, str) and isinstance(v2, str):
                v1_parts = [int(x) for x in v1.split('.')]
                v2_parts = [int(x) for x in v2.split('.')]
                for a, b in zip(v1_parts, v2_parts):
                    if a > b:
                        return v1
                    elif b > a:
                        return v2
                return v1
        except Exception:
            pass
        return v2
