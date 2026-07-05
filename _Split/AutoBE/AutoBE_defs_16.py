class AutoBEApp:
    
    def _merge_json(self, _json_list, _file_name):
        # Use simple union merge for entity files to preserve all custom features
        if _file_name.endswith('.entity.json') or 'entity' in _file_name.lower():
            return self._merge_entity_json_simple(_json_list, _file_name)
        
        def normalize_string(s):
            try:
                s = _re.sub(r'\\s*=\\s*', '=', s)
                s = s.replace("1st_person", "first_person").replace("3rd_person", "third_person")
                s = s.replace("v.is_first_person", "variable.is_first_person").replace("q.is_spectator", "query.is_spectator")
                return s
            except Exception as e:
                print(f"Error normalizing string '{s}': {e}")
                return s

        def remove_duplicates_from_list(_list, check_keys=False):
            unique_list = []
            seen = set()
            for item in _list:
                try:
                    if isinstance(item, str):
                        normalized_item = normalize_string(item)
                        if normalized_item not in seen:
                            unique_list.append(item)
                            seen.add(normalized_item)
                    elif isinstance(item, dict):
                        normalized_dict = {normalize_string(k): normalize_string(v) if isinstance(v, str) else v for k, v in item.items()}
                        item_tuple = tuple(sorted(normalized_dict.keys())) if check_keys else tuple(sorted(normalized_dict.items()))
                        if item_tuple not in seen:
                            unique_list.append(item)
                            seen.add(item_tuple)
                except Exception as e:
                    print(f"Error processing item '{item}': {e}")
            return unique_list

        def merge_dicts(merged_dict, new_dict):
            for k, v in new_dict.items():
                try:
                    norm_key = normalize_string(k)
                    if norm_key in merged_dict:
                        if isinstance(merged_dict[norm_key], dict) and isinstance(v, dict):
                            merged_dict[norm_key] = self._merge_json([merged_dict[norm_key], v], _file_name)
                        elif isinstance(merged_dict[norm_key], list) and isinstance(v, list):
                            check_keys = _file_name == "player.json" and norm_key in ['render_controllers', 'animations', 'animate', 'particle_effects']
                            merged_dict[norm_key] = remove_duplicates_from_list(merged_dict[norm_key] + v, check_keys)
                        else:
                            if normalize_string(str(v)) != normalize_string(str(merged_dict[norm_key])):
                                print(f"Duplicate detected and removed: {_file_name}: {k}")
                    else:
                        merged_dict[norm_key] = v
                except Exception as e:
                    print(f"Error processing key '{k}' with value '{v}': {e}")
            return merged_dict

        _merged = {}
        _format_version_set = False
        _format_version = None
        _warning_shown = False  # Flag to track if the warning has been shown

        # Dictionary to track MCPACK format versions
        mcpack_versions = {}
        differing_mcpack_names = set()  # Track MCPACK names with different format versions

        # Use the MCPACK names from _add_files
        mcpack_names = getattr(self, 'mcpack_names', [])

        # Process each JSON object
        for index, _json in enumerate(_json_list):
            try:
                if 'format_version' in _json:
                    current_version = _json['format_version']
                    # Track format_version for each MCPACK
                    mcpack_name = mcpack_names[index] if index < len(mcpack_names) else 'Unknown MCPACK'
                    if mcpack_name in mcpack_versions:
                        if mcpack_versions[mcpack_name] != current_version:
                            differing_mcpack_names.add(mcpack_name)
                    mcpack_versions[mcpack_name] = current_version
                    
                    if not _format_version_set:
                        _format_version = current_version
                        _format_version_set = True
                    elif current_version != _format_version:
                        # Update the set of differing MCPACK names
                        differing_mcpack_names.add(mcpack_name)

                for _key, _value in _json.items():
                    if _key == "format_version" and not _format_version_set:
                        _merged[_key] = _value
                        _format_version_set = True
                    elif _file_name in ("player.animation_controllers.json", "player.render_controllers.json", "player.animation.json"):
                        # For animation/render controller files use first-wins per named entry.
                        # Deep-merging two incompatible animation state machines produces broken results
                        # (e.g. sideways first-person camera). Keep the first pack's definition for any
                        # controller/animation name that already exists; add unique names from later packs.
                        if _key not in _merged:
                            _merged[_key] = _value
                        elif isinstance(_merged[_key], dict) and isinstance(_value, dict):
                            for _sub_k, _sub_v in _value.items():
                                if _sub_k not in _merged[_key]:  # first-wins per named entry
                                    _merged[_key][_sub_k] = _sub_v
                        elif isinstance(_merged[_key], list) and isinstance(_value, list):
                            _merged[_key] = remove_duplicates_from_list(_merged[_key] + _value)
                    elif _file_name == "_ui_defs.json":
                        if _key not in _merged:
                            _merged[_key] = _value
                        else:
                            if isinstance(_value, list):
                                if not isinstance(_merged[_key], list):
                                    _merged[_key] = [_merged[_key]]
                                _merged[_key].extend(_value)
                                _merged[_key] = remove_duplicates_from_list(_merged[_key])
                            elif isinstance(_value, str):
                                if isinstance(_merged[_key], list):
                                    normalized_value = normalize_string(_value)
                                    existing_values = [normalize_string(i) for i in _merged[_key]]
                                    if normalized_value not in existing_values:
                                        _merged[_key].append(_value)
                                else:
                                    _merged[_key] = [_merged[_key], _value]
                            else:
                                _merged[_key] = _value
                    elif _file_name == "player.json":
                        if _key not in _merged:
                            _merged[_key] = _value
                        else:
                            if isinstance(_value, list):
                                check_keys = _key in ['render_controllers', 'animations', 'animate', 'particle_effects']
                                merged_list = _merged[_key] + _value
                                _merged[_key] = remove_duplicates_from_list(merged_list, check_keys)
                            elif isinstance(_merged[_key], dict) and isinstance(_value, dict):
                                _merged[_key] = self._merge_json([_merged[_key], _value], _file_name)
                            else:
                                _merged[_key] = _value
                    elif _file_name in ("item_texture.json", "terrain_texture.json"):
                        if _key not in _merged:
                            _merged[_key] = _value
                        elif _key == "texture_data" and isinstance(_merged[_key], dict) and isinstance(_value, dict):
                            # First-wins: only add texture entries not already present so earlier packs' textures are preserved
                            for _tk, _tv in _value.items():
                                if _tk not in _merged[_key]:
                                    _merged[_key][_tk] = _tv
                        elif isinstance(_merged[_key], dict) and isinstance(_value, dict):
                            _merged[_key] = self._merge_json([_merged[_key], _value], _file_name)
                        elif isinstance(_merged[_key], list) and isinstance(_value, list):
                            _merged[_key] = remove_duplicates_from_list(_merged[_key] + _value)
                    elif _file_name == "crafting_item_catalog.json":
                        # Merge crafting/creative catalog: union groups by category_name
                        if _key not in _merged:
                            _merged[_key] = _value
                        elif _key == "minecraft:crafting_items_catalog" and isinstance(_merged[_key], dict) and isinstance(_value, dict):
                            merged_cat = _merged[_key]
                            new_cat = _value
                            if "categories" in new_cat:
                                if "categories" not in merged_cat:
                                    merged_cat["categories"] = []
                                # Index existing categories by category_name
                                _existing = {c.get("category_name"): c for c in merged_cat["categories"] if isinstance(c, dict)}
                                for _nc in new_cat["categories"]:
                                    if not isinstance(_nc, dict): continue
                                    _cname = _nc.get("category_name")
                                    if _cname in _existing:
                                        # Union the groups lists — append new groups not already present by icon
                                        _eg = _existing[_cname].setdefault("groups", [])
                                        _existing_icons = {g.get("group_identifier", {}).get("icon") for g in _eg if isinstance(g, dict)}
                                        for _ng in _nc.get("groups", []):
                                            if isinstance(_ng, dict):
                                                _icon = _ng.get("group_identifier", {}).get("icon")
                                                if _icon not in _existing_icons:
                                                    _eg.append(_ng)
                                                    _existing_icons.add(_icon)
                                    else:
                                        merged_cat["categories"].append(_nc)
                                        _existing[_cname] = _nc
                        elif isinstance(_merged[_key], dict) and isinstance(_value, dict):
                            _merged[_key] = self._merge_json([_merged[_key], _value], _file_name)
                    elif _file_name == "sound_definitions.json":
                        if _key not in _merged:
                            _merged[_key] = _value
                        elif _key == "sound_definitions" and isinstance(_merged[_key], dict) and isinstance(_value, dict):
                            # First-wins: preserve existing sound entries; add new ones from later packs
                            for _sk, _sv in _value.items():
                                if _sk not in _merged[_key]:
                                    _merged[_key][_sk] = _sv
                                elif isinstance(_merged[_key][_sk], dict) and isinstance(_sv, dict):
                                    # Union the sounds arrays so both packs' sound files are included
                                    existing_sounds = _merged[_key][_sk].get("sounds", [])
                                    new_sounds = _sv.get("sounds", [])
                                    if isinstance(existing_sounds, list) and isinstance(new_sounds, list):
                                        combined = existing_sounds + [s for s in new_sounds if s not in existing_sounds]
                                        _merged[_key][_sk]["sounds"] = combined
                        elif isinstance(_merged[_key], dict) and isinstance(_value, dict):
                            _merged[_key] = self._merge_json([_merged[_key], _value], _file_name)
                    elif _file_name == "hud_screen.json":
                        # Special handling for hud_screen.json to preserve modifications arrays
                        if _key not in _merged:
                            _merged[_key] = _value
                        elif isinstance(_merged[_key], dict) and isinstance(_value, dict):
                            # Recursively merge dictionaries, but concatenate modifications arrays
                            if _key == "modifications" and isinstance(_merged[_key], list) and isinstance(_value, list):
                                # Concatenate modifications arrays to preserve all UI injection operations
                                _merged[_key] = _merged[_key] + _value
                            else:
                                _merged[_key] = self._merge_json([_merged[_key], _value], _file_name)
                        elif isinstance(_merged[_key], list) and isinstance(_value, list):
                            # Concatenate lists for hud_screen.json
                            _merged[_key] = _merged[_key] + _value
                        else:
                            _merged[_key] = _value
                    else:
                        # Enhanced merging for entity files and other common conflict files
                        if _key not in _merged:
                            _merged[_key] = _value
                        else:
                            # Special handling for entity file properties that should be merged
                            if _file_name.endswith('.json') and _key in ['components', 'component_groups', 'events', 'spawn_rules', 'behaviors']:
                                # These properties should be merged, not overwritten
                                if isinstance(_merged[_key], dict) and isinstance(_value, dict):
                                    # Merge components/component_groups/events dictionaries
                                    _merged[_key] = self._merge_json([_merged[_key], _value], _file_name)
                                elif isinstance(_merged[_key], list) and isinstance(_value, list):
                                    # Merge spawn_rules/behaviors lists
                                    merged_list = _merged[_key] + _value
                                    _merged[_key] = remove_duplicates_from_list(merged_list, check_keys=True)
                                else:
                                    # Fallback: try to merge if types match
                                    if type(_merged[_key]) == type(_value):
                                        if isinstance(_value, dict):
                                            _merged[_key] = self._merge_json([_merged[_key], _value], _file_name)
                                        elif isinstance(_value, list):
                                            merged_list = _merged[_key] + _value
                                            _merged[_key] = remove_duplicates_from_list(merged_list, check_keys=True)
                                        else:
                                            _merged[_key] = _value
                                    else:
                                        _merged[_key] = _value
                            elif isinstance(_merged[_key], list) and isinstance(_value, list):
                                # Merge lists by combining and removing duplicates
                                merged_list = _merged[_key] + _value
                                _merged[_key] = remove_duplicates_from_list(merged_list, check_keys=True)
                            elif isinstance(_merged[_key], dict) and isinstance(_value, dict):
                                # Recursively merge dictionaries
                                _merged[_key] = self._merge_json([_merged[_key], _value], _file_name)
                            else:
                                # For primitive values, keep the last one (but log if different)
                                if str(_merged[_key]) != str(_value) and _key not in ['format_version', 'description']:
                                    # UI visibility conditions must be combined, not overwritten.
                                    # If Pack A says "(not 'mqps')" and Pack B says "(not '!')",
                                    # the merged pack should hide text matching EITHER prefix.
                                    if (_key == 'visible'
                                            and 'hud_screen' in _file_name
                                            and isinstance(_merged[_key], str)
                                            and isinstance(_value, str)):
                                        _merged[_key] = f'({_merged[_key]}) && ({_value})'
                                    else:
                                        _merged[_key] = _value
            except Exception as e:
                print(f"Error processing JSON data for file '{_file_name}': {e}")

        # blocks.json post-processing: strip legacy geometry/shape specs from
        # custom-namespace block entries so they don't clash with minecraft:geometry
        # components defined in the block's own JSON, which produces in-game warnings.
        if _file_name == "blocks.json":
            _LEGACY_SHAPE_KEYS = {"geometry", "carried_textures", "isotropic", "brightness_gamma"}
            for _bk in list(_merged.keys()):
                if ':' in _bk and not _bk.startswith('minecraft:') and isinstance(_merged[_bk], dict):
                    for _lk in _LEGACY_SHAPE_KEYS:
                        _merged[_bk].pop(_lk, None)

        # Client entity post-processing: strip empty-string keys from geometry/textures/materials
        # to prevent Molang errors like "geometry. not found in entity friendly name list"
        if _file_name.endswith('.entity.json') or _file_name.endswith('.entity.json'.replace('entity.', 'client_entity.')):
            for _root_key in ('minecraft:client_entity', 'minecraft:entity'):
                _desc = _merged.get(_root_key, {}).get('description', {})
                for _sect in ('geometry', 'textures', 'materials', 'animations'):
                    if _sect in _desc and isinstance(_desc[_sect], dict):
                        _desc[_sect] = {k: v for k, v in _desc[_sect].items() if v not in ('', None)}

        return _merged
    
    def _merge_player_json(self, _player_json_list, file_path=None):
        """Merge player JSON files using universal merger for intelligent conflict resolution."""
        merger = UniversalJsonMerger()
        return merger.merge_json_list(_player_json_list, file_path=file_path)

    def _merge_dicts(self, _dict1, _dict2):
        for _key, _value in _dict2.items():
            if _key in _dict1:
                if isinstance(_dict1[_key], dict) and isinstance(_value, dict):
                    _dict1[_key] = self._merge_dicts(_dict1[_key], _value)
                elif isinstance(_dict1[_key], list) and isinstance(_value, list):
                    _dict1[_key].extend(_value)
                else:
                    _dict1[_key] = _value
            else:
                _dict1[_key] = _value
        return _dict1

    def _merge_lang_files(self, _lang_list):
        _merged_lang = {}   # key -> value (first-wins)
        _comment_lines = [] # preserve ## comment/section lines from first pack only
        _seen_comments = set()
        for _idx, _lang_data in enumerate(_lang_list):
            for _line in _lang_data.splitlines():
                _stripped = _line.strip()
                if not _stripped:
                    continue
                if _stripped.startswith('##'):
                    # Only keep comment lines from the first pack to avoid duplicated section headers
                    if _idx == 0 and _stripped not in _seen_comments:
                        _comment_lines.append((_stripped, len(_merged_lang)))
                        _seen_comments.add(_stripped)
                    continue
                if '=' in _stripped:
                    _key, _value = _stripped.split('=', 1)
                    _key = _key.strip()
                    if _key and _key not in _merged_lang:  # first-wins
                        _merged_lang[_key] = _value
        # Build output: interleave comment lines at their original positions
        _kv_pairs = [f"{k}={v}" for k, v in _merged_lang.items()]
        _output_lines = []
        _comment_idx = 0
        for _i, _pair in enumerate(_kv_pairs):
            while _comment_idx < len(_comment_lines) and _comment_lines[_comment_idx][1] <= _i:
                _output_lines.append(_comment_lines[_comment_idx][0])
                _comment_idx += 1
            _output_lines.append(_pair)
        # Append any trailing comment lines
        while _comment_idx < len(_comment_lines):
            _output_lines.append(_comment_lines[_comment_idx][0])
            _comment_idx += 1
        return '\n'.join(_output_lines)

    def _load_json_with_comments(self, _file):
        """Load JSON file with robust comment and error handling. Uses same logic as _get_manifest_data."""
        try:
            # Read the file content - try UTF-8 first, fallback to latin-1
            try:
                _file_content = _file.read().decode('utf-8')
            except UnicodeDecodeError:
                _file_content = _file.read().decode('latin-1', errors='ignore')
            
            # Try json5 first (handles comments natively)
            json5_available = True
            try:
                import json5 as _json5
            except ImportError:
                json5_available = False
                _logging.warning("json5 library not installed, attempting manual comment removal.")
            
            if json5_available:
                try:
                    return _json5.loads(_file_content)
                except Exception as json5_error:
                    # json5 failed, try with cleaned content
                    _logging.warning(f"json5 parsing failed for {_file.name}, attempting cleanup: {json5_error}")
                    # Fall through to manual comment removal
            
            # Fallback: try to remove comments manually
            # Remove block comments /* ... */ (non-greedy)
            _file_content_clean = _re.sub(r'/\*.*?\*/', '', _file_content, flags=_re.DOTALL)
            
            # Remove line comments // ... (but not in strings)
            lines = _file_content_clean.split('\n')
            cleaned_lines = []
            for line in lines:
                # Find // that's not inside a string
                in_string = False
                escape_next = False
                new_line = []
                i = 0
                while i < len(line):
                    char = line[i]
                    if escape_next:
                        new_line.append(char)
                        escape_next = False
                    elif char == '\\' and in_string:
                        new_line.append(char)
                        escape_next = True
                    elif char == '"' and not escape_next:
                        in_string = not in_string
                        new_line.append(char)
                    elif char == '/' and i + 1 < len(line) and line[i+1] == '/' and not in_string:
                        # Found // comment outside string
                        break
                    else:
                        new_line.append(char)
                    i += 1
                cleaned_lines.append(''.join(new_line))
            _file_content_clean = '\n'.join(cleaned_lines)
            
            # Remove trailing commas before closing braces/brackets
            _file_content_clean = _re.sub(r',\s*([}\]])', r'\1', _file_content_clean)
            
            # Try parsing with standard json
            try:
                return _json.loads(_file_content_clean)
            except Exception as json_error:
                _logging.warning(f"Error parsing JSON (after cleanup) in file: {_file.name}: {json_error}")
                _logging.info(f"Attempting JSON extraction for {_file.name}...")
                # Last resort: try to extract just the JSON structure
                try:
                    # Find first { and matching closing }
                    start_idx = _file_content_clean.find('{')
                    if start_idx >= 0:
                        # Count braces to find the matching closing brace
                        brace_count = 0
                        in_string = False
                        escape_next = False
                        i = start_idx
                        while i < len(_file_content_clean):
                            char = _file_content_clean[i]
                            if escape_next:
                                escape_next = False
                            elif char == '\\' and in_string:
                                escape_next = True
                            elif char == '"' and not escape_next:
                                in_string = not in_string
                            elif not in_string:
                                if char == '{':
                                    brace_count += 1
                                elif char == '}':
                                    brace_count -= 1
                                    if brace_count == 0:
                                        # Found matching closing brace
                                        json_str = _file_content_clean[start_idx:i+1]
                                        return _json.loads(json_str)
                            i += 1
                except Exception as extract_error:
                    _logging.error(f"Failed to extract JSON from {_file.name}: {extract_error}")
            
            return None
        except Exception as e:
            _logging.error(f"Error reading or parsing JSON file: {_file.name}: {e}")
            return None

    def _get_manifest_data(self, _file):
        """Extract and parse manifest.json from a pack file. Handles JSON with comments using json5."""
        try:
            with _zipfile.ZipFile(_file, 'r') as _pack_zip:
                # Try to find manifest.json (case-insensitive, may be in root or subdirectory)
                # Prefer root level, then behavior_pack (for .mcaddon script-version grouping), then any subdirectory
                manifest_path = None
                root_manifest = None
                behavior_pack_manifest = None
                first_subdir_manifest = None
                for name in _pack_zip.namelist():
                    name_lower = name.lower()
                    if name_lower == 'manifest.json':
                        root_manifest = name
                        break
                    if name_lower.endswith('/manifest.json'):
                        if first_subdir_manifest is None:
                            first_subdir_manifest = name
                        if 'behavior_pack' in name_lower:
                            behavior_pack_manifest = name
                
                if root_manifest:
                    manifest_path = root_manifest
                elif behavior_pack_manifest:
                    manifest_path = behavior_pack_manifest
                elif first_subdir_manifest:
                    manifest_path = first_subdir_manifest

                # ── Nested .mcpack fallback (common .mcaddon layout) ─────────
                # .mcaddon files usually contain .mcpack zip entries rather than
                # raw files, so manifest.json lives inside those inner archives.
                if not manifest_path:
                    import io as _io
                    _inner_candidates = [
                        n for n in _pack_zip.namelist()
                        if n.lower().endswith(('.mcpack', '.zip')) and '/' not in n
                    ]
                    # Prefer a BP entry, then any entry
                    _inner_candidates.sort(
                        key=lambda x: (0 if any(k in x.lower() for k in ('behavior', '_bp', 'bp_')) else 1)
                    )
                    for _inner_name in _inner_candidates:
                        try:
                            with _pack_zip.open(_inner_name) as _inner_data:
                                _inner_bytes = _inner_data.read()
                            with _zipfile.ZipFile(_io.BytesIO(_inner_bytes), 'r') as _inner_zip:
                                for _iname in _inner_zip.namelist():
                                    if _iname.lower() == 'manifest.json':
                                        with _inner_zip.open(_iname) as _imf:
                                            _raw = _imf.read()
                                        try:
                                            _mc = _raw.decode('utf-8')
                                        except UnicodeDecodeError:
                                            _mc = _raw.decode('latin-1', errors='ignore')
                                        try:
                                            import json5 as _json5
                                            return _json5.loads(_mc)
                                        except Exception:
                                            pass
                                        try:
                                            return _json.loads(_mc)
                                        except Exception:
                                            pass
                                        break
                        except Exception:
                            continue

                if manifest_path:
                    with _pack_zip.open(manifest_path) as _manifest_file:
                        try:
                            # Read the manifest file content - try UTF-8 first, fallback to latin-1
                            try:
                                _manifest_content = _manifest_file.read().decode('utf-8')
                            except UnicodeDecodeError:
                                _manifest_content = _manifest_file.read().decode('latin-1', errors='ignore')
                            
                            # Use json5 library which natively supports comments
                            # No need to manually remove comments - json5 handles them
                            # Try json5 first (handles comments natively)
                            json5_available = True
                            try:
                                import json5 as _json5
                            except ImportError:
                                json5_available = False
                                _logging.warning("json5 library not installed, attempting manual comment removal.")
                            
                            if json5_available:
                                try:
                                    _manifest_data = _json5.loads(_manifest_content)
                                    return _manifest_data
                                except Exception as json5_error:
                                    # json5 failed, try with cleaned content
                                    _logging.warning(f"json5 parsing failed for {_file}, attempting cleanup: {json5_error}")
                                    # Fall through to manual comment removal
                            
                            # Fallback: try to remove comments manually
                            # Remove block comments /* ... */ (non-greedy)
                            _manifest_content_clean = _re.sub(r'/\*.*?\*/', '', _manifest_content, flags=_re.DOTALL)
                            
                            # Remove line comments // ... (but not in strings)
                            lines = _manifest_content_clean.split('\n')
                            cleaned_lines = []
                            for line in lines:
                                # Find // that's not inside a string
                                in_string = False
                                escape_next = False
                                new_line = []
                                i = 0
                                while i < len(line):
                                    char = line[i]
                                    if escape_next:
                                        new_line.append(char)
                                        escape_next = False
                                    elif char == '\\' and in_string:
                                        new_line.append(char)
                                        escape_next = True
                                    elif char == '"' and not escape_next:
                                        in_string = not in_string
                                        new_line.append(char)
                                    elif char == '/' and i + 1 < len(line) and line[i+1] == '/' and not in_string:
                                        # Found // comment outside string
                                        break
                                    else:
                                        new_line.append(char)
                                    i += 1
                                cleaned_lines.append(''.join(new_line))
                            _manifest_content_clean = '\n'.join(cleaned_lines)
                            
                            # Remove trailing commas before closing braces/brackets
                            _manifest_content_clean = _re.sub(r',\s*([}\]])', r'\1', _manifest_content_clean)
                            
                            # Try parsing with standard json
                            try:
                                _manifest_data = _json.loads(_manifest_content_clean)
                                return _manifest_data
                            except Exception as json_error:
                                _logging.warning(f"Error parsing manifest.json (after cleanup) in file: {_file}: {json_error}")
                                _logging.info(f"Attempting JSON extraction for {_file}...")
                                # Last resort: try to extract just the JSON structure
                                try:
                                    # Find first { and matching closing }
                                    start_idx = _manifest_content_clean.find('{')
                                    if start_idx >= 0:
                                        # Count braces to find the matching closing brace
                                        brace_count = 0
                                        end_idx = start_idx
                                        in_string = False
                                        escape_next = False
                                        
                                        for i in range(start_idx, len(_manifest_content_clean)):
                                            char = _manifest_content_clean[i]
                                            if escape_next:
                                                escape_next = False
                                            elif char == '\\' and in_string:
                                                escape_next = True
                                            elif char == '"' and not escape_next:
                                                in_string = not in_string
                                            elif not in_string:
                                                if char == '{':
                                                    brace_count += 1
                                                elif char == '}':
                                                    brace_count -= 1
                                                    if brace_count == 0:
                                                        end_idx = i
                                                        break
                                        
                                        if end_idx > start_idx and brace_count == 0:
                                            extracted_json = _manifest_content_clean[start_idx:end_idx+1]
                                            _manifest_data = _json.loads(extracted_json)
                                            _logging.info(f"Successfully extracted and parsed JSON for {_file}")
                                            return _manifest_data
                                        else:
                                            _logging.error(f"Could not find matching braces for {_file} (start: {start_idx}, end: {end_idx}, brace_count: {brace_count})")
                                except Exception as extract_error:
                                    _logging.error(f"JSON extraction failed for {_file}: {extract_error}")
                                return None
                        except Exception as e:
                            _logging.error(f"Error reading manifest.json in file: {_file}: {e}")
                            return None
                else:
                    _logging.warning(f"manifest.json not found in file: {_file}")
                    return None
        except _zipfile.BadZipFile:
            _logging.error(f"Invalid ZIP file: {_file}")
            return None
        except Exception as e:
            _logging.error(f"Error opening file: {_file}: {e}")
            return None
        
        return None

    def _create_manifest(self):
        # Persist BP/RP header UUIDs for this output directory so they remain stable
        # across re-merges.  Bedrock stores the UUID in world_behavior_packs.json;
        # if the UUID changes every merge the world keeps running the old (stale) pack.
        _uuid_cache_path = _os.path.join(self._out_dir, ".autobe_uuids.json")
        _uuid_cache = {}
        try:
            if _os.path.isfile(_uuid_cache_path):
                with open(_uuid_cache_path, 'r', encoding='utf-8') as _uf:
                    _uuid_cache = _json.load(_uf)
        except Exception:
            _uuid_cache = {}

        def _stable_uuid(key):
            if key not in _uuid_cache or not _uuid_cache[key]:
                _uuid_cache[key] = str(_uuid.uuid4())
            return _uuid_cache[key]

        _bp_header_uuid = _stable_uuid("bp_header")
        _rp_header_uuid = _stable_uuid("rp_header")
        _bp_module_uuid = _stable_uuid("bp_module")
        _rp_module_uuid = _stable_uuid("rp_module")

        try:
            with open(_uuid_cache_path, 'w', encoding='utf-8') as _uf:
                _json.dump(_uuid_cache, _uf, indent=2)
        except Exception:
            pass

        # Retrieve highest versions found during extraction
        highest_bp_version = getattr(self, 'highest_bp_version', None)
        highest_rp_version = getattr(self, 'highest_rp_version', None)
        highest_server_version_full = getattr(self, 'highest_server_version_full', "1.13.0")
        highest_server_ui_version_full = getattr(self, 'highest_server_ui_version_full', "1.2.0")
        highest_gametest_version_full = getattr(self, 'highest_gametest_version_full', None)

        # Minimum required version for Minecraft Bedrock (1.13.0 is the minimum)
        min_required_version = [1, 13, 0]
        # Default fallback version (only used if no versions were found at all)
        default_version = [1, 21, 30]

        def compare_versions(version_a, version_b):
            """Compares two versions (assumed to be lists of integers). Returns True if version_a >= version_b"""
            if version_a is None:
                return False
            if version_b is None:
                return True
            for i in range(3):
                if version_a[i] > version_b[i]:
                    return True
                elif version_a[i] < version_b[i]:
                    return False
            return True  # Equal versions

        # Use the highest found version, ensuring it's at least the minimum required
        if highest_bp_version is None:
            # No version found, use default
            highest_bp_version = default_version
        elif not compare_versions(highest_bp_version, min_required_version):
            # Version found but below minimum, use minimum
            highest_bp_version = min_required_version

        if highest_rp_version is None:
            # No version found, use default
            highest_rp_version = default_version
        elif not compare_versions(highest_rp_version, min_required_version):
            # Version found but below minimum, use minimum
            highest_rp_version = min_required_version

        # Behavior Pack Manifest
        _manifest_behavior = {
            "format_version": 2,
            "header": {
                "description": "Modpack Created Using AutoBE - CodeNex",
                "name": "AutoBE Behavior",
                "uuid": _bp_header_uuid,
                "version": [1, 0, 0],
                "min_engine_version": highest_bp_version
            },
            "modules": [
                {
                    "description": "Created Using AutoBE - CodeNex",
                    "type": "data",
                    "uuid": _bp_module_uuid,
                    "version": [1, 0, 0]
                },
                {
                    "description": "gametesting",
                    "language": "javascript",
                    "type": "script",
                    "uuid": str(_uuid.uuid4()),
                    "version": [1, 0, 0],
                    "entry": "scripts/CodeNex.js"
                }
            ],
            "capabilities": ["script_eval"],
            "dependencies": [
                {
                    "uuid": _rp_header_uuid,
                    "version": [1, 0, 0]
                },
                {
                    "module_name": "@minecraft/server",
                    "version": highest_server_version_full
                },
                {
                    "module_name": "@minecraft/server-ui",
                    "version": highest_server_ui_version_full
                }
            ],
            "metadata": {
                "authors": ["CodeNex"]
            }
        }

        # Add @minecraft/server-gametest dependency if a version was found
        if highest_gametest_version_full:
            _manifest_behavior["dependencies"].append({
                "module_name": "@minecraft/server-gametest",
                "version": highest_gametest_version_full
            })

        # Resource Pack Manifest
        _manifest_resource = {
            "format_version": 2,
            "header": {
                "description": "Modpack Created Using AutoBE - CodeNex",
                "name": "AutoBE Resource",
                "uuid": _rp_header_uuid,
                "version": [1, 0, 0],
                "min_engine_version": highest_rp_version
            },
            "modules": [
                {
                    "description": "Created Using AutoBE - CodeNex",
                    "type": "resources",
                    "uuid": _rp_module_uuid,
                    "version": [1, 0, 0]
                }
            ],
            "dependencies": [
                {
                    "uuid": _bp_header_uuid,
                    "version": [1, 0, 0]
                }
            ],
            "metadata": {
                "authors": ["CodeNex"]
            }
        }

        # Paths for the pack files
        _bp_path = _os.path.join(self._out_dir, "behavior_pack.zip")
        _rp_path = _os.path.join(self._out_dir, "resource_pack.zip")

        # Find the first available pack_icon from source packs to use for both output packs
        _icon_bytes = None
        try:
            for _src in getattr(self, '_files', []):
                if _icon_bytes:
                    break
                try:
                    with _zipfile.ZipFile(_src, 'r') as _sz:
                        for _n in _sz.namelist():
                            _nb = _n.lower().split('/')[-1]
                            if _nb in ('pack_icon.png', 'pack_icon.jpg', 'pack_icon.jpeg'):
                                _icon_bytes = _sz.read(_n)
                                break
                except Exception:
                    pass
        except Exception:
            pass

        try:
            # Write behavior pack manifest to zip
            with _zipfile.ZipFile(_bp_path, 'a') as _bp_zip:
                _bp_zip.writestr("manifest.json", _json.dumps(_manifest_behavior, indent=2))
                if _icon_bytes:
                    _bp_zip.writestr("pack_icon.png", _icon_bytes)

            # Write resource pack manifest to zip
            with _zipfile.ZipFile(_rp_path, 'a') as _rp_zip:
                _rp_zip.writestr("manifest.json", _json.dumps(_manifest_resource, indent=2))
                if _icon_bytes:
                    _rp_zip.writestr("pack_icon.png", _icon_bytes)

            # Convert zip files to .mcpack files
            _bp_new_path = _os.path.join(self._out_dir, "behavior_pack.mcpack")
            _shutil.move(_bp_path, _bp_new_path)

            _rp_new_path = _os.path.join(self._out_dir, "resource_pack.mcpack")
            _shutil.move(_rp_path, _rp_new_path)

        except Exception as e:
            log_error(e)
            _messagebox.showerror("Error", f"An error occurred during manifest creation: {str(e)}")

    def _move_tick_and_delete_functions(self):
        _functions_folder = _os.path.join(self._out_dir, "functions")
        _entities_folder = _os.path.join(self._out_dir, "entities")
        
        _bp_path = _os.path.join(self._out_dir, "behavior_pack.mcpack")
        _rp_path = _os.path.join(self._out_dir, "resource_pack.mcpack")

        _bp_functions_folder = "functions"
        _rp_functions_folder = f"{_bp_functions_folder}/"
        
        _bp_entities_folder = "entities"
        _rp_entities_folder = f"{_bp_entities_folder}/"

        _bp_tick_path = f"{_bp_functions_folder}/tick.json"
        _rp_tick_path = f"{_rp_functions_folder}tick.json"
        
        _bp_player_path = f"{_bp_entities_folder}/player.json"
        _rp_player_path = f"{_rp_entities_folder}player.json"

        try:
            # Move tick.json from resource pack to behavior pack
            with _zipfile.ZipFile(_rp_path, 'r') as _rp_zip:
                with _zipfile.ZipFile(_bp_path, 'a') as _bp_zip:
                    try:
                        _tick_data = _rp_zip.read(_rp_tick_path)
                        _bp_zip.writestr(_bp_tick_path, _tick_data)
                    except KeyError:
                        _logging.debug(f"'{_rp_tick_path}' not found in resource pack.")
                    
                    try:
                        _player_data = _rp_zip.read(_rp_player_path)
                        _bp_zip.writestr(_bp_player_path, _player_data)
                    except KeyError:
                        _logging.debug(f"'{_rp_player_path}' not found in resource pack.")

        except Exception as _e:
            _logging.error(f"An error occurred during the initial file operations: {_e}")

        try:
            # Extract and delete functions folder
            with _zipfile.ZipFile(_rp_path, 'a') as _rp_zip:
                for _file in list(_rp_zip.namelist()):
                    if _file.startswith(_rp_functions_folder):
                        try:
                            _rp_zip.extract(_file, self._out_dir)
                            _os.remove(_os.path.join(self._out_dir, _file))
                        except FileNotFoundError:
                            _logging.warning(f"File '{_file}' not found during extraction.")
                try:
                    _shutil.rmtree(_functions_folder)
                except FileNotFoundError:
                    _logging.debug(f"Folder '{_functions_folder}' not found during removal.")

        except Exception as _e:
            _logging.error(f"An error occurred while processing functions folder: {_e}")

        try:
            # Extract and delete entities folder
            with _zipfile.ZipFile(_rp_path, 'a') as _rp_zip:
                for _file in list(_rp_zip.namelist()):
                    if _file.startswith(_rp_entities_folder):
                        try:
                            _rp_zip.extract(_file, self._out_dir)
                            _os.remove(_os.path.join(self._out_dir, _file))
                        except FileNotFoundError:
                            _logging.warning(f"File '{_file}' not found during extraction.")
                try:
                    _shutil.rmtree(_entities_folder)
                except FileNotFoundError:
                    _logging.debug(f"Folder '{_entities_folder}' not found during removal.")

        except Exception as _e:
            _messagebox.showinfo("Error", f"An error occurred: {_e}")

    def _delete_manifest_files(self):
        _packs = ["behavior_pack.zip", "resource_pack.zip"]

        for _pack in _packs:
            _pack_path = _os.path.join(self._out_dir, _pack)
            _temp_pack_path = _os.path.join(self._out_dir, f"temp_{_pack}")

            try:
                with _zipfile.ZipFile(_pack_path, 'r') as _zip_read:
                    with _zipfile.ZipFile(_temp_pack_path, 'w') as _zip_write:
                        for _item in _zip_read.infolist():
                            if _item.filename not in ["manifest.json", "package.json", "contents.json", ".data", "package-lock.json", "signatures.json"]:
                                _data = _zip_read.read(_item.filename)
                                _zip_write.writestr(_item, _data)

                _os.remove(_pack_path)
                _os.rename(_temp_pack_path, _pack_path)

            except _zipfile.BadZipFile:
                _logging.error(f"Bad ZIP file: {_pack_path}", exc_info=True)
                _messagebox.showerror("Error", f"Bad ZIP file: {_pack_path}")
            except FileNotFoundError:
                _logging.warning(f"File not found: {_pack_path}")
            except Exception as _e:
                pass

    def _move_and_cleanup(self):
        _bp_path = _os.path.join(self._out_dir, "Behavior_packs", "scripts", "scripts")
        _mainjs_path = _os.path.join(self._out_dir, "Behavior_packs", "scripts", "CodeNex.js")
        _scriptswe_path = _os.path.join(self._out_dir, "scripts")

        try:
            _dest_scripts = _os.path.join(self._out_dir, "scripts")
            if _os.path.isdir(_bp_path):
                if _os.path.isdir(_dest_scripts):
                    _shutil.rmtree(_dest_scripts)
                _shutil.move(_bp_path, self._out_dir)
        except FileNotFoundError:
            print(f"Directory '{_bp_path}' does not exist.")

        try:
            if _os.path.exists(_scriptswe_path) and not _os.path.isdir(_scriptswe_path):
                _os.remove(_scriptswe_path)  # remove stale file artefact before makedirs
            _os.makedirs(_scriptswe_path, exist_ok=True)
            _dest_js = _os.path.join(_scriptswe_path, _os.path.basename(_mainjs_path))
            if _os.path.exists(_mainjs_path):
                if _os.path.exists(_dest_js):
                    _os.remove(_dest_js)
                _shutil.move(_mainjs_path, _scriptswe_path)
        except FileNotFoundError:
            print(f"File '{_mainjs_path}' does not exist.")

        try:
            _bp_path = _os.path.join(self._out_dir, "Behavior_packs")
            _shutil.rmtree(_bp_path)
        except FileNotFoundError:
            print(f"Directory '{_bp_path}' does not exist.")
