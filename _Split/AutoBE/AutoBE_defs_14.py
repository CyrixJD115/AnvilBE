class AutoBEApp:

    def _process_packs(self, _files, _output_dir):
        _output_zip_path_resource = _os.path.join(_output_dir, "resource_pack.zip")
        _output_zip_path_behavior = _os.path.join(_output_dir, "behavior_pack.zip")

        _json_contents_resource = {}
        _json_contents_behavior = {}
        _lang_contents_resource = {}
        _lang_contents_behavior = {}
        _material_contents = {}
        _mcfunction_contents = {}
        _written_feature_rules = {}  # basename -> arcname already written

        _text_json_contents_resource = {}
        # First-wins tracking for binary assets so earlier packs' textures/sounds are not
        # overwritten by later packs' files at the same path.
        _written_paths_resource = set()
        _written_paths_behavior = set()

        # Dictionary to store player-related JSON data
        _player_json_contents_resource = {}  # For resource packs (entity folder)
        _player_json_contents_behavior = {}  # For behavior packs (entities folder)
        
        # Dictionary to store entity files grouped by identifier for intelligent merging
        # Format: {identifier: {file_path: json_data}}
        _entity_files_by_identifier_resource = {}  # For resource packs (entity folder)
        _entity_files_by_identifier_behavior = {}  # For behavior packs (entities folder)
        
        # Dictionary to store item/block files grouped by identifier
        _item_files_by_identifier = {}  # For items
        _block_files_by_identifier = {}  # For blocks

        _mergeable_files = {
            "item_texture.json", "terrain_texture.json", "tick.json", "sounds.json", "blocks.json",
            "biomes_client.json", "sound_definitions.json", "music_definitions.json",
            "_ui_defs.json", "hud_screen.json", "npc_interact_screen.json", 
            "_global_variables.json", "ui_common.json", "splashes.json",
            "player.animation_controllers.json", "player.animation.json", "player.render_controllers.json",
            "crafting_item_catalog.json",
        }
        # List-type JSON files: arrays that must be union-merged rather than dict-merged
        _list_mergeable_files = {"flipbook_textures.json", "textures_list.json"}
        _list_json_contents_resource = {}   # path -> combined list entries

        # Initialize identifier conflict resolution system for universal addon compatibility
        identifier_manager = None
        try:
            identifier_manager = IdentifierManager()
            # First pass: Scan all packs for identifiers to detect conflicts
            all_pack_identifiers = {}
            for scan_file in _files:
                scan_file_path = scan_file
                if _os.path.isdir(scan_file_path):
                    # For directories, create a temp zip to scan
                    temp_zip_path = _os.path.join(_output_dir, f"temp_scan_{_os.path.basename(scan_file_path)}.mcpack")
                    with _zipfile.ZipFile(temp_zip_path, 'w', _zipfile.ZIP_DEFLATED) as zf:
                        for root, dirs, files in _os.walk(scan_file_path):
                            for file in files:
                                file_path = _os.path.join(root, file)
                                arcname = _os.path.relpath(file_path, scan_file_path)
                                zf.write(file_path, arcname)
                    scan_file_path = temp_zip_path
                
                try:
                    with _zipfile.ZipFile(scan_file_path, 'r') as scan_zip:
                        all_pack_identifiers[scan_file] = identifier_manager.scan_pack_identifiers(scan_zip, scan_file)
                except Exception as e:
                    _logging.warning(f"Could not scan identifiers from {scan_file}: {e}")
            
            # Detect conflicts; optionally show UI for user to choose which pack to keep per conflict
            if all_pack_identifiers:
                identifier_manager.detect_conflicts(all_pack_identifiers)
                conflict_list = identifier_manager.get_conflict_list()
                if conflict_list:
                    self._set_discord_merge_step(
                        f"Resolving {len(conflict_list)} conflict{'s' if len(conflict_list) != 1 else ''}",
                        "Waiting for user input"
                    )
                    _conflict_done = threading.Event()
                    def _show_conflict_ui():
                        self._show_conflict_resolution_overlay(conflict_list, identifier_manager, _conflict_done)
                    if threading.current_thread() is threading.main_thread():
                        _show_conflict_ui()
                    else:
                        self._root.after(0, _show_conflict_ui)
                        _conflict_done.wait()
                identifier_manager.generate_identifier_mappings()
                _logging.info(f"Identifier conflict resolution initialized: {len(identifier_manager.identifier_mapping)} mappings created")
        except Exception as e:
            _logging.warning(f"Identifier manager initialization failed (merging will continue without conflict resolution): {e}")
            identifier_manager = None

        self._progress['value'] = 0
        self._progress['maximum'] = 100  # always 0-100 so _update_progress percentages are correct

        _merge_start_ts = int(_datetime.datetime.now().timestamp())
        self._discord_merge_last_update = 0  # reset rate limiter so first pack always shows

        _total_files = len(_files)
        for _i, _file in enumerate(_files):
            # Update step label and progress bar for each pack (Step 2 occupies 25-50 range)
            _pack_label = _os.path.basename(_file).replace('_modified', '')
            if len(_pack_label) > 55:
                _pack_label = _pack_label[:52] + '...'
            _step2_pct = 25 + int((_i / max(_total_files, 1)) * 25)  # 25% -> 50%
            try:
                self._progress['value'] = _step2_pct
                self._progress_step_label.config(
                    text=f"Step 2/4: Processing {_i + 1}/{_total_files} — {_pack_label}")
                self._root.update_idletasks()
            except Exception:
                pass
            # Update Discord RPC with current pack (rate-limited to once per 15 s inside method)
            self._update_discord_merge_progress(_pack_label, _i + 1, _total_files, _merge_start_ts)

            # If _file is a folder, zip it up as a .mcpack and process as usual
            if _os.path.isdir(_file):
                # Only treat as a pack if manifest.json and pack_icon are at the root
                manifest_path = _os.path.join(_file, 'manifest.json')
                has_icon = any(_os.path.isfile(_os.path.join(_file, f'pack_icon{ext}')) for ext in ['.png', '.jpg', '.jpeg'])
                if not (_os.path.isfile(manifest_path) and has_icon):
                    _logging.warning(f"Skipping {_file} - not a valid pack folder.")
                    continue
                # Zip the folder into a temp .mcpack
                temp_mcpack = _os.path.join(_output_dir, f"temp_{_os.path.basename(_file)}.mcpack")
                with _zipfile.ZipFile(temp_mcpack, 'w', _zipfile.ZIP_DEFLATED) as zf:
                    for root, dirs, files in _os.walk(_file):
                        # If we find a subfolder named 'subpacks', copy it as-is (do not iterate into it for manifests/icons)
                        rel_root = _os.path.relpath(root, _file)
                        if rel_root == 'subpacks':
                            for subpack_name in dirs:
                                subpack_path = _os.path.join(root, subpack_name)
                                for sub_root, sub_dirs, sub_files in _os.walk(subpack_path):
                                    for sub_file in sub_files:
                                        abs_path = _os.path.join(sub_root, sub_file)
                                        arcname = _os.path.relpath(abs_path, _file)
                                        zf.write(abs_path, arcname)
                            # Skip further walk into subpacks
                            dirs.clear()
                        else:
                            for file in files:
                                abs_path = _os.path.join(root, file)
                                arcname = _os.path.relpath(abs_path, _file)
                                zf.write(abs_path, arcname)
                _file = temp_mcpack  # Now process as a .mcpack file

            _manifest_data = self._get_manifest_data(_file)
            if not _manifest_data:
                _logging.warning(f"Skipping {_file} - manifest.json not found or invalid.")
                continue

            _module_type = _manifest_data.get("modules", [{}])[0].get("type", "")

            with _zipfile.ZipFile(_file, 'r') as _pack_zip:
                _pack_names = _pack_zip.namelist()
                _has_r_prefix = any(name.startswith('R/') for name in _pack_names)
                _has_b_prefix = any(name.startswith('B/') for name in _pack_names)
                _is_mcaddon_layout = _has_r_prefix or _has_b_prefix

                # Normalise module type: map resource-like variants to "resources" and
                # behaviour-like variants to "data" so packs with non-standard types
                # (e.g. "client_data", "javascript", "") are never silently skipped.
                _resource_types = {"resources", "client_data"}
                _behavior_types = {"data", "script", "javascript", "data_driven"}
                if _module_type in _resource_types:
                    _module_type = "resources"
                elif _module_type in _behavior_types:
                    _module_type = "data"
                elif not _is_mcaddon_layout:
                    # Unknown type on a plain pack: try to infer from folder structure
                    _pack_has_textures = any(n.startswith('textures/') for n in _pack_names)
                    _pack_has_entities_bp = any(n.startswith('entities/') for n in _pack_names)
                    if _pack_has_textures and not _pack_has_entities_bp:
                        _module_type = "resources"
                        _logging.warning(f"Unknown module type '{_module_type}' in {_file} — treating as resources (has textures/).")
                    else:
                        _module_type = "data"
                        _logging.warning(f"Unknown module type in {_file} — treating as data.")
                # For mcaddon layout, default to resources so _output_zip is set
                if _is_mcaddon_layout and _module_type not in {"resources", "data"}:
                    _module_type = "resources"

                with _zipfile.ZipFile(_output_zip_path_resource, 'a') as _output_zip_resource, _zipfile.ZipFile(_output_zip_path_behavior, 'a') as _output_zip_behavior:
                    # ExtendedBE pack-level fixers: run once per source pack with full zip access.
                    # These can analyse cross-file relationships and inject brand-new files
                    # (e.g. missing block definitions, corrected manifests) into the merged output.
                    _ebe_pack_extra = {"rp": {}, "bp": {}}
                    _ebe_pack_on = (
                        _EXTENDEDBE_FIXERS and
                        getattr(getattr(self, 'extendedbe_enabled_var', None), 'get', lambda: False)()
                    )
                    if _ebe_pack_on:
                        try:
                            _ebe_pack_extra = _extendedbe.apply_pack_fixers(
                                _EXTENDEDBE_FIXERS, _os.path.basename(_file), _pack_zip)
                        except Exception as _ebe_pe:
                            _logging.warning(f"[ExtendedBE] apply_pack_fixers error: {_ebe_pe}")
                    _last_ui_update = _time.monotonic()
                    _file_idx_in_pack = 0
                    for _item in _pack_zip.infolist():
                        _item_name = _item.filename
                        _file_idx_in_pack += 1
                        # Throttled UI refresh: update label every ~0.4 s so the user can see
                        # the app is alive even during long single-pack processing.
                        _now = _time.monotonic()
                        if _now - _last_ui_update >= 0.4:
                            _last_ui_update = _now
                            _short_name = _item_name if len(_item_name) <= 45 else '...' + _item_name[-42:]
                            try:
                                self._progress_step_label.config(
                                    text=f"Step 2/4: Pack {_i + 1}/{_total_files} — {_pack_label}\n↳ {_short_name}")
                                self._root.update_idletasks()
                            except Exception:
                                pass
                        _effective_module_type = _module_type
                        _output_zip = _output_zip_resource if _effective_module_type == "resources" else _output_zip_behavior

                        if _is_mcaddon_layout:
                            if _item_name.startswith('R/'):
                                _effective_module_type = "resources"
                                _output_zip = _output_zip_resource
                                _item_name = _item_name[2:]
                            elif _item_name.startswith('B/'):
                                _effective_module_type = "data"
                                _output_zip = _output_zip_behavior
                                _item_name = _item_name[2:]
                            else:
                                # Skip root-level files in mcaddon containers to avoid leaking R/B manifests into outputs
                                continue

                        # Skip source manifests and icons — the output pack gets its own generated manifest
                        _item_base_lower = _item_name.lower().split('/')[-1]
                        if _item_name.lower() == 'manifest.json' or _item_name.lower().endswith('/manifest.json'):
                            continue
                        if _item_base_lower in ('pack_icon.png', 'pack_icon.jpg', 'pack_icon.jpeg'):
                            continue
                        # Exclude ui/server_form.json from merged RPs.  Packs like BetterCombat
                        # ship a partial server_form.json that overrides vanilla form rendering
                        # but omits the 'long_form_panel' component, making all ActionFormData
                        # forms (including Lorewarden's menus) show only a dark background with
                        # no content.  The vanilla game engine has a complete built-in version;
                        # removing custom overrides lets all server UI forms render correctly.
                        if _effective_module_type == 'resources' and _item_base_lower == 'server_form.json':
                            continue

                        # If this is a subpacks/ file or folder, just copy as-is, do not process for manifests/icons
                        if _item_name.startswith('subpacks/'):
                            self._copy_to_zip(_pack_zip, _item, _output_zip, None, _file, identifier_manager, _override_name=_item_name,
                                              _written_paths=_written_paths_resource if _output_zip is _output_zip_resource else _written_paths_behavior)
                            continue
                        if _item_name.startswith("feature_rules"):
                            _fr_base = _os.path.basename(_item_name)
                            if _fr_base and not _fr_base.endswith('/'):
                                if _fr_base not in _written_feature_rules:
                                    _fr_arc = f"feature_rules/{_fr_base}"
                                    _written_feature_rules[_fr_base] = _fr_arc
                                else:
                                    # Collision: prefix with a short pack token to keep both rules
                                    _fr_tok = _re.sub(r'[^a-z0-9]', '', _os.path.basename(_file).lower())[:8]
                                    _fr_arc = f"feature_rules/{_fr_tok}_{_fr_base}"
                                with _pack_zip.open(_item) as _fr_data:
                                    _output_zip.writestr(_fr_arc, _fr_data.read())
                            continue
                        if _item_name.endswith(".json"):
                            if _effective_module_type == "resources" and _item_name.startswith("texts/"):
                                with _pack_zip.open(_item) as _json_file:
                                    try:
                                        _json_data = self._load_json_with_comments(_json_file)
                                        # Accept both dict (e.g. texts/en_US.json) and list
                                        # (e.g. texts/languages.json = ["en_US", ...]) so the
                                        # union-merge write loop actually processes them.
                                        if _json_data is not None:
                                            _text_json_contents_resource.setdefault(_item_name, []).append(_json_data)
                                            continue
                                    except Exception:
                                        pass
                            # Check if the JSON file is in the 'entity' or 'entities' folder
                            if _os.path.dirname(_item_name) in {"entity", "entities"}:
                                with _pack_zip.open(_item) as _json_file:
                                    try:
                                        _json_data = self._load_json_with_comments(_json_file)
                                        # Update identifiers in entity files if manager is available
                                        if identifier_manager:
                                            try:
                                                _json_data = identifier_manager.update_json_identifiers(_json_data, _file)
                                            except Exception as e:
                                                _logging.warning(f"Error updating entity identifiers in {_item_name}: {e}")
                                        # Check for 'minecraft:client_entity' -> 'description' -> 'identifier'
                                        client_entity = _json_data.get("minecraft:client_entity")
                                        if client_entity and isinstance(client_entity, dict):
                                            description = client_entity.get("description")
                                            if description and isinstance(description, dict):
                                                identifier = description.get("identifier")
                                                if identifier == "minecraft:player":
                                                    # Store player-related JSON data for merging
                                                    _player_json_contents_resource.setdefault(_item_name, []).append(_json_data)
                                                    continue  # Skip copying this file directly
                                    except _json.JSONDecodeError:
                                        _logging.warning(f"Failed to parse JSON file: {_item_name}")
                            # Handle other JSON files
                            if _os.path.basename(_item_name) not in _mergeable_files:
                                # For entity/item/block files, collect by identifier for intelligent merging
                                dir_name = _os.path.dirname(_item_name)
                                if dir_name in {"entities", "entity", "items", "blocks"}:
                                    try:
                                        with _pack_zip.open(_item) as _json_file:
                                            _json_data = self._load_json_with_comments(_json_file)
                                            # ExtendedBE: apply per-file fixer before identifier-based collection.
                                            # Entity/item/block files never reach _copy_to_zip so fixers must run here.
                                            if (_EXTENDEDBE_FIXERS and _file and
                                                    getattr(getattr(self, 'extendedbe_enabled_var', None), 'get', lambda: False)()):
                                                try:
                                                    _jb_id = _json.dumps(_json_data, indent=2).encode('utf-8')
                                                    _, _jb_id_out = _extendedbe.apply_fixers(
                                                        _EXTENDEDBE_FIXERS, _os.path.basename(_file), _item_name, _jb_id)
                                                    if _jb_id_out != _jb_id:
                                                        _json_data = _json.loads(_jb_id_out.decode('utf-8'))
                                                except Exception as _ebe_id_e:
                                                    _logging.warning(f"[ExtendedBE] fixer error on {_item_name}: {_ebe_id_e}")

                                            # Extract identifier BEFORE renaming (we need original identifier for grouping)
                                            # This allows us to merge entities with the same identifier
                                            if dir_name in {"entities", "entity"}:
                                                entity_id = self._extract_entity_identifier_from_json(_json_data)
                                                if entity_id:
                                                    if identifier_manager and not identifier_manager.should_include_definition(_file, entity_id):
                                                        continue  # User chose to keep another pack's definition
                                                    entity_dict = _entity_files_by_identifier_behavior if _effective_module_type in {"data", "script"} else _entity_files_by_identifier_resource
                                                    if entity_id not in entity_dict:
                                                        entity_dict[entity_id] = []
                                                    entity_dict[entity_id].append({
                                                        'file_path': _item_name,
                                                        'data': _json_data,
                                                        'pack_path': _file,
                                                        'original_id': entity_id
                                                    })
                                                    continue  # Skip copying - will be merged later
                                                else:
                                                    # No identifier — if it's player.json in a BP, accumulate for merge
                                                    if _os.path.basename(_item_name) == 'player.json' and _effective_module_type in {"data", "script"}:
                                                        _player_json_contents_behavior.setdefault(_item_name, []).append(_json_data)
                                                    else:
                                                        self._copy_to_zip(_pack_zip, _item, _output_zip, _json_data, _file, identifier_manager, _override_name=_item_name)
                                            elif dir_name == "items":
                                                item_id = self._extract_item_identifier_from_json(_json_data)
                                                if item_id:
                                                    if identifier_manager and not identifier_manager.should_include_definition(_file, item_id):
                                                        continue
                                                    if item_id not in _item_files_by_identifier:
                                                        _item_files_by_identifier[item_id] = []
                                                    _item_files_by_identifier[item_id].append({
                                                        'file_path': _item_name,
                                                        'data': _json_data,
                                                        'pack_path': _file,
                                                        'original_id': item_id
                                                    })
                                                    continue  # Skip copying - will be merged later
                                                else:
                                                    self._copy_to_zip(_pack_zip, _item, _output_zip, _json_data, _file, identifier_manager, _override_name=_item_name)
                                            elif dir_name == "blocks":
                                                block_id = self._extract_block_identifier_from_json(_json_data)
                                                if block_id:
                                                    if identifier_manager and not identifier_manager.should_include_definition(_file, block_id):
                                                        continue
                                                    if block_id not in _block_files_by_identifier:
                                                        _block_files_by_identifier[block_id] = []
                                                    _block_files_by_identifier[block_id].append({
                                                        'file_path': _item_name,
                                                        'data': _json_data,
                                                        'pack_path': _file,
                                                        'original_id': block_id
                                                    })
                                                    continue  # Skip copying - will be merged later
                                                else:
                                                    self._copy_to_zip(_pack_zip, _item, _output_zip, _json_data, _file, identifier_manager, _override_name=_item_name)
                                    except Exception as e:
                                        _logging.warning(f"Error processing {_item_name}: {e}")
                                        self._copy_to_zip(_pack_zip, _item, _output_zip, None, _file, identifier_manager, _override_name=_item_name,
                                                          _written_paths=_written_paths_resource if _output_zip is _output_zip_resource else _written_paths_behavior)
                                else:
                                    self._copy_to_zip(_pack_zip, _item, _output_zip, None, _file, identifier_manager, _override_name=_item_name,
                                                      _written_paths=_written_paths_resource if _output_zip is _output_zip_resource else _written_paths_behavior)
                            elif _os.path.basename(_item_name) in _list_mergeable_files and _effective_module_type == "resources":
                                # flipbook_textures.json / textures_list.json are top-level arrays;
                                # collect all entries for union merge instead of dict merge.
                                with _pack_zip.open(_item) as _jf:
                                    try:
                                        _jd = self._load_json_with_comments(_jf)
                                        if isinstance(_jd, list):
                                            _list_json_contents_resource.setdefault(_item_name, []).extend(_jd)
                                        elif isinstance(_jd, dict):
                                            self._handle_json_item(_pack_zip, _item, _json_contents_resource, _output_zip, _effective_module_type, _file, identifier_manager, _override_name=_item_name)
                                    except Exception:
                                        pass
                            else:
                                # ExtendedBE: run per-file fixers on mergeable files (sounds.json etc.)
                                # before they're collected for dict-merge, so invalid entries are removed
                                # from each source before they can pollute the merged output.
                                _ebe_mf_injected = False
                                if (_EXTENDEDBE_FIXERS and _file and
                                        getattr(getattr(self, 'extendedbe_enabled_var', None), 'get', lambda: False)()):
                                    try:
                                        with _pack_zip.open(_item) as _mf_fh:
                                            _mf_bytes = _mf_fh.read()
                                        _, _mf_fixed = _extendedbe.apply_fixers(
                                            _EXTENDEDBE_FIXERS, _os.path.basename(_file), _item_name, _mf_bytes)
                                        if _mf_fixed != _mf_bytes:
                                            _mf_fixed_json = _json.loads(_mf_fixed.decode('utf-8'))
                                            _collect = (_json_contents_resource if _effective_module_type == "resources"
                                                        else _json_contents_behavior)
                                            _collect.setdefault(_item_name, []).append(_mf_fixed_json)
                                            _ebe_mf_injected = True
                                    except Exception as _ebe_mfe:
                                        _logging.warning(f"[ExtendedBE] mergeable fixer error on {_item_name}: {_ebe_mfe}")
                                if not _ebe_mf_injected:
                                    self._handle_json_item(_pack_zip, _item,
                                        _json_contents_resource if _effective_module_type == "resources" else _json_contents_behavior,
                                        _output_zip, _effective_module_type, _file, identifier_manager, _override_name=_item_name)
                        elif _item_name.endswith(".lang"):
                            with _pack_zip.open(_item) as _lang_file:
                                _raw = _lang_file.read()
                                try:
                                    _lang_data = _raw.decode('utf-8')
                                except Exception:
                                    _lang_data = _raw.decode('latin-1', errors='ignore')
                                _lang_data = strip_bom(_lang_data)
                                # Apply identifier renames to lang keys so they stay in sync
                                if identifier_manager:
                                    try:
                                        _lang_data = identifier_manager.update_text_identifiers(_lang_data, _file)
                                    except Exception:
                                        pass
                                # Lang files always go into the resource pack regardless of pack type:
                                # Minecraft reads display-name translations from the RP.  Many addon
                                # creators only ship lang files inside their BP, so we mirror them to
                                # the RP as well to ensure names resolve in-game.
                                _lang_contents_resource.setdefault(_item_name, []).append(_lang_data)
                                # Also keep BP lang in the behavior pack for script access
                                if _effective_module_type in {"data", "script"}:
                                    _lang_contents_behavior.setdefault(_item_name, []).append(_lang_data)
                        elif _item_name.endswith(".material"):
                            self._handle_json_item(_pack_zip, _item, _material_contents, _output_zip, _effective_module_type, _file, identifier_manager)
                        elif _item_name.endswith(".mcfunction"):
                            with _pack_zip.open(_item) as _mcfunction_file:
                                try:
                                    _mcfunction_data = _mcfunction_file.read().decode('utf-8')
                                except UnicodeDecodeError:
                                    _mcfunction_data = _mcfunction_file.read().decode('latin-1')
                                _mcfunction_data = strip_bom(_mcfunction_data)
                                # Update identifiers in mcfunction files
                                if identifier_manager:
                                    try:
                                        _mcfunction_data = identifier_manager.update_text_identifiers(_mcfunction_data, _file)
                                    except Exception as e:
                                        _logging.warning(f"Error updating identifiers in {_item_name}: {e}")
                                _mcfunction_contents.setdefault(_item_name, []).append(_mcfunction_data)
                        else:
                            # Binary files: textures (.png), sounds (.ogg/.fsb), structures (.mcstructure),
                            # shaders, and any other non-text assets that don't need merging.
                            # First-wins: if two packs ship a file at the same path, keep the first.
                            self._copy_to_zip(
                                _pack_zip, _item, _output_zip, None, _file, identifier_manager,
                                _override_name=_item_name,
                                _written_paths=_written_paths_resource if _output_zip is _output_zip_resource else _written_paths_behavior)

                    # Write any new files injected by pack-level fixers.
                    for _xp, _xb in _ebe_pack_extra.get("rp", {}).items():
                        try:
                            _output_zip_resource.writestr(_xp, _xb)
                        except Exception as _xe:
                            _logging.warning(f"[ExtendedBE] failed to inject RP file {_xp}: {_xe}")
                    for _xp, _xb in _ebe_pack_extra.get("bp", {}).items():
                        try:
                            _output_zip_behavior.writestr(_xp, _xb)
                        except Exception as _xe:
                            _logging.warning(f"[ExtendedBE] failed to inject BP file {_xp}: {_xe}")

            self._progress['value'] = _i + 1
            try:
                self._root.update_idletasks()
            except Exception:
                pass

        if _list_json_contents_resource:
            with _zipfile.ZipFile(_output_zip_path_resource, 'a') as _output_zip:
                for _list_file, _list_entries in _list_json_contents_resource.items():
                    # Deduplicate by converting to a stable string key
                    _seen_keys = set()
                    _unique_entries = []
                    for _entry in _list_entries:
                        try:
                            _key = _json.dumps(_entry, sort_keys=True)
                        except Exception:
                            _key = str(_entry)
                        if _key not in _seen_keys:
                            _seen_keys.add(_key)
                            _unique_entries.append(_entry)
                    _output_zip.writestr(_list_file, _json.dumps(_unique_entries, indent=2, ensure_ascii=False))

        if _text_json_contents_resource:
            with _zipfile.ZipFile(_output_zip_path_resource, 'a') as _output_zip:
                for _json_file, _json_list in _text_json_contents_resource.items():
                    # Check if the data is list-based (e.g. texts/languages.json = ["en_US", ...])
                    _first_non_none = next((d for d in _json_list if d is not None), None)
                    if isinstance(_first_non_none, list):
                        # Union merge: collect all unique string entries across all packs
                        _merged_list = []
                        _seen_entries = set()
                        for _data in _json_list:
                            if not isinstance(_data, list):
                                continue
                            for _entry in _data:
                                if isinstance(_entry, str) and _entry not in _seen_entries:
                                    _merged_list.append(_entry)
                                    _seen_entries.add(_entry)
                        _output_zip.writestr(_json_file, _json.dumps(_merged_list, indent=2, ensure_ascii=False))
                    else:
                        _merged = {}
                        for _data in _json_list:
                            if not isinstance(_data, dict):
                                continue
                            for _k, _v in _data.items():
                                if _k not in _merged:
                                    _merged[_k] = _v
                        _output_zip.writestr(_json_file, _json.dumps(_merged, indent=2, ensure_ascii=False))

        # Vanilla player animation aliases used as a safe fallback baseline.
        # These are injected (setdefault) into the merged player entity so that
        # animation controllers which reference standard vanilla short names
        # (e.g. "crouch", "bob", "riding.arms") always resolve even when no
        # addon explicitly includes them in their player entity modifications.
        _VANILLA_PLAYER_ANIMS = {
            "root":                           "controller.animation.player.root",
            "move":                           "animation.player.move",
            "riding.arms":                    "animation.player.riding.arms",
            "riding.legs":                    "animation.player.riding.legs",
            "holding":                        "animation.player.holding",
            "brandish_spear":                 "animation.player.brandish_spear",
            "holding_spyglass":               "animation.player.holding_spyglass",
            "charging":                       "animation.player.charging",
            "attack.positions":               "animation.player.attack.positions",
            "attack.rotations":               "animation.player.attack.rotations",
            "sneaking":                       "animation.player.sneaking",
            "crouch":                         "animation.player.sneaking",
            "bob":                            "animation.player.bob",
            "damage_nearby_mobs":             "animation.player.damage_nearby_mobs",
            "fishing_rod":                    "animation.player.fishing_rod",
            "swimming":                       "animation.player.swimming",
            "swimming.legs":                  "animation.player.swimming.legs",
            "use_item_progress":              "animation.player.use_item_progress",
            "skeleton_attack":                "animation.player.skeleton_attack",
            "sleeping":                       "animation.player.sleeping",
            "cape":                           "animation.player.cape",
            "first_person_base_pose":         "animation.player.first_person_base_pose",
            "first_person_empty_hand":        "animation.player.first_person_empty_hand",
            "first_person_swap_item":         "animation.player.first_person_swap_item",
            "first_person_attack_controller": "controller.animation.player.first_person_attack",
            "first_person_map_controller":    "controller.animation.player.first_person_map",
            "first_person_crossbow_equipped": "animation.player.first_person_crossbow_equipped",
            "first_person_breathing_bob":     "animation.player.first_person_breathing_bob",
            "third_person_bow":               "animation.player.third_person_bow",
            "third_person_crossbow":          "animation.player.third_person_crossbow",
            "third_person_die":               "animation.player.third_person_die",
            "third_person_map_controller":    "controller.animation.player.third_person_map",
            "blink":                          "controller.animation.player.blink",
            "totem_animation":                "animation.player.totem",
            "totem_controller":               "controller.animation.player.totem",
            "look_at_target_ui":              "animation.player.look_at_target.ui",
            "look_at_target_default":         "animation.player.look_at_target.default",
            "look_at_target_gliding":         "animation.player.look_at_target.gliding",
            "look_at_target_swimming":        "animation.player.look_at_target.swimming",
            "look_at_target_inverted":        "animation.player.look_at_target.inverted",
        }

        # Scan ALL player-related animation/controller files for variables that are used but
        # never assigned.  Done unconditionally so the scan runs even when no pack in this
        # group supplies an entity/player.json (e.g. the 'none' group only has an RP half).
        _anim_var_undefined = set()
        _RUNTIME_VARS = {
            'is_holding_left': (
                'variable.is_holding_left = '
                '!query.is_item_name_any(\'slot.weapon.offhand\', 0, \'minecraft:air\');'
            ),
            'player_arm_height': 'variable.player_arm_height = 0.0;',
            'short_arm_offset_left': 'variable.short_arm_offset_left = 0.0;',
            'short_arm_offset_right': 'variable.short_arm_offset_right = 0.0;',
            'is_horizontal_splitscreen': 'variable.is_horizontal_splitscreen = 0.0;',
            'is_vertical_splitscreen': 'variable.is_vertical_splitscreen = 0.0;',
        }
        try:
            _anim_used = set()
            for _key, _datalist in _json_contents_resource.items():
                _is_player_anim = (
                    ('animation_controllers' in _key and 'player' in _key) or
                    ('animations' in _key and 'player' in _key and
                     not _key.endswith('_controllers.json'))
                )
                if not _is_player_anim:
                    continue
                _text = _json.dumps(_datalist)
                _anim_used.update(
                    _re.findall(r'variable\.([a-zA-Z_][a-zA-Z0-9_]*)', _text))
            # All used variables are candidates for injection; the _already filter
            # (built from the merged entity's actual initialize/pre_animation blocks)
            # is the correct gate — not _anim_assigned, which fires on assignments inside
            # animation states and incorrectly marks variables as "initialised".
            _anim_var_undefined = _anim_used
        except Exception:
            pass

        # Merge player-related JSON files for resource packs (entity folder)
        if _player_json_contents_resource:
            merged_player_data = {}
            for _item_name, _json_data_list in _player_json_contents_resource.items():
                for _json_data in _json_data_list:
                    self._merge_json_data(merged_player_data, _json_data)

            # Inject any undefined animation variables into the merged entity/player.json
            try:
                if _anim_var_undefined:
                    _desc = (merged_player_data
                             .setdefault('minecraft:client_entity', {})
                             .setdefault('description', {}))
                    _scripts = _desc.setdefault('scripts', {})
                    _init    = _scripts.setdefault('initialize', [])
                    _pre     = _scripts.setdefault('pre_animation', [])
                    _existing_text = (' '.join(str(x) for x in _init) + ' ' +
                                      ' '.join(str(x) for x in _pre))
                    _already = set(_re.findall(r'variable\.([a-zA-Z_][a-zA-Z0-9_]*)\s*=',
                                               _existing_text))
                    for _vname in sorted(_anim_var_undefined - _already):
                        if _vname in _RUNTIME_VARS:
                            _pre.append(_RUNTIME_VARS[_vname])
                        else:
                            _init.append(f"variable.{_vname} = 0.0;")
            except Exception:
                pass

            # ── Post-merge fixes on the merged RP player entity ──────────────
            # Each fix has its own try/except so one failure cannot silence the rest.
            _pe_desc = {}
            try:
                _pe_desc = (merged_player_data
                            .get('minecraft:client_entity', {})
                            .get('description', {}))
            except Exception:
                pass

            # 1. Sanitize known-bad Molang slot names.
            try:
                _BAD_SLOTS = {
                    "'slot.mainhand'":         "'slot.weapon.mainhand'",
                    '"slot.mainhand"':         '"slot.weapon.mainhand"',
                    "'slot.offhand'":          "'slot.weapon.offhand'",
                    '"slot.offhand"':          '"slot.weapon.offhand"',
                }
                for _sblk in ('initialize', 'pre_animation'):
                    _slist = _pe_desc.get('scripts', {}).get(_sblk, [])
                    if not isinstance(_slist, list):
                        continue
                    for _si, _sexpr in enumerate(_slist):
                        if isinstance(_sexpr, str):
                            for _bad, _good in _BAD_SLOTS.items():
                                _sexpr = _sexpr.replace(_bad, _good)
                            _slist[_si] = _sexpr
            except Exception:
                pass

            # 2. Move entity-context queries out of 'initialize' into 'pre_animation'.
            #    query.is_item_name_any / query.property / query.equipped_item_any_tag
            #    all require entity context that initialize does not have.
            try:
                _ENTITY_CTX_QUERIES = (
                    'query.is_item_name_any',
                    'query.is_item_any_tag',
                    'query.equipped_item_any_tag',
                    'query.property(',
                    'query.has_equippable(',
                    'query.get_equipped_item_name(',
                )
                _scripts_dict  = _pe_desc.setdefault('scripts', {})
                _init_list_raw = _scripts_dict.get('initialize', [])
                _init_list     = list(_init_list_raw) if isinstance(_init_list_raw, list) else []
                _pre_list      = _scripts_dict.setdefault('pre_animation', [])
                if not isinstance(_pre_list, list):
                    _pre_list = []
                    _scripts_dict['pre_animation'] = _pre_list
                _keep_init, _move_to_pre = [], []
                for _expr in _init_list:
                    if isinstance(_expr, str) and any(q in _expr for q in _ENTITY_CTX_QUERIES):
                        _move_to_pre.append(_expr)
                    else:
                        _keep_init.append(_expr)
                if _move_to_pre:
                    _scripts_dict['initialize'] = _keep_init
                    _existing_pre_text = ' '.join(str(x) for x in _pre_list)
                    for _mv in _move_to_pre:
                        if _mv not in _existing_pre_text:
                            _pre_list.append(_mv)
            except Exception:
                pass

            # 3. Backfill missing vanilla animation aliases.
            try:
                _anims_dict = _pe_desc.setdefault('animations', {})
                if not isinstance(_anims_dict, dict):
                    _anims_dict = {}
                    _pe_desc['animations'] = _anims_dict
                for _alias, _anim_id in _VANILLA_PLAYER_ANIMS.items():
                    _anims_dict.setdefault(_alias, _anim_id)
            except Exception:
                pass

            # 4. Stub any animation short-names in scripts.animate that are not
            #    defined in the merged animations dict.
            try:
                _animate_block = _pe_desc.get('scripts', {}).get('animate', [])
                if not isinstance(_animate_block, list):
                    _animate_block = []
                _defined_aliases = set(_anims_dict.keys()) if isinstance(_anims_dict, dict) else set()
                for _entry in _animate_block:
                    _aname = None
                    if isinstance(_entry, str):
                        _aname = _entry.strip()
                    elif isinstance(_entry, dict):
                        _aname = next(iter(_entry), None)
                    if _aname and _aname not in _defined_aliases:
                        _anims_dict[_aname] = "animation.player.move"
                        _defined_aliases.add(_aname)
            except Exception:
                pass

            # 5. De-duplicate scripts.animate by name (dict-with-condition beats plain string).
            try:
                _scripts_blk = _pe_desc.get('scripts', {})
                _anim_blk2 = _scripts_blk.get('animate', [])
                if isinstance(_anim_blk2, list):
                    _anim_seen2 = {}
                    for _ae2 in _anim_blk2:
                        if isinstance(_ae2, str):
                            if _ae2 not in _anim_seen2:
                                _anim_seen2[_ae2] = _ae2
                        elif isinstance(_ae2, dict) and _ae2:
                            _ak2 = next(iter(_ae2))
                            _anim_seen2[_ak2] = _ae2  # dict wins over any earlier plain string
                    _scripts_blk['animate'] = list(_anim_seen2.values())
            except Exception:
                pass

            # 6. De-duplicate render_controllers by controller name (first occurrence wins).
            try:
                _rc_list2 = _pe_desc.get('render_controllers', [])
                if isinstance(_rc_list2, list):
                    _rc_seen2 = {}
                    for _rce2 in _rc_list2:
                        if isinstance(_rce2, dict) and _rce2:
                            _rcn2 = next(iter(_rce2))
                            if _rcn2 not in _rc_seen2:
                                _rc_seen2[_rcn2] = _rce2
                        elif isinstance(_rce2, str) and _rce2 not in _rc_seen2:
                            _rc_seen2[_rce2] = _rce2
                    _pe_desc['render_controllers'] = list(_rc_seen2.values())
            except Exception:
                pass

            with _zipfile.ZipFile(_output_zip_path_resource, 'a') as _output_zip:
                _output_zip.writestr("entity/player.entity.json", _json.dumps(merged_player_data, indent=2))
        

        if _anim_var_undefined:
            # No pack in this group supplied an entity/player.json but animation controllers
            # reference uninitialized variables.  Write a minimal client-entity stub so
            # Molang doesn't error on the first frame.
            try:
                _stub_init = []
                _stub_pre  = []
                for _vname in sorted(_anim_var_undefined):
                    if _vname in _RUNTIME_VARS:
                        _stub_pre.append(_RUNTIME_VARS[_vname])
                    else:
                        _stub_init.append(f"variable.{_vname} = 0.0;")
                _stub = {
                    "format_version": "1.10.0",
                    "minecraft:client_entity": {
                        "description": {
                            "identifier": "minecraft:player",
                            "animations": dict(_VANILLA_PLAYER_ANIMS),
                            "scripts": {}
                        }
                    }
                }
                _stub_scripts = _stub["minecraft:client_entity"]["description"]["scripts"]
                if _stub_init:
                    _stub_scripts["initialize"] = _stub_init
                if _stub_pre:
                    _stub_scripts["pre_animation"] = _stub_pre
                with _zipfile.ZipFile(_output_zip_path_resource, 'a') as _output_zip:
                    _output_zip.writestr("entity/player.entity.json", _json.dumps(_stub, indent=2))
            except Exception:
                pass

        # Merge player-related JSON files for behavior packs (entities folder)
        if _player_json_contents_behavior:
            merged_player_data = {}
            for _item_name, _json_data_list in _player_json_contents_behavior.items():
                for _json_data in _json_data_list:
                    self._merge_json_data(merged_player_data, _json_data)
            with _zipfile.ZipFile(_output_zip_path_behavior, 'a') as _output_zip:
                _output_zip.writestr("entities/player.json", _json.dumps(merged_player_data, indent=2))
        
        # Merge entity files by identifier (intelligent merging - same entity from multiple addons)
        # IMPORTANT: When merging entities with the same identifier, we keep the original identifier
        # and merge their components. We only rename identifiers if they're different entities.
        
        # Resource packs (entity folder)
        with _zipfile.ZipFile(_output_zip_path_resource, 'a') as _output_zip:
            for entity_id, entity_list in _entity_files_by_identifier_resource.items():
                if len(entity_list) > 1:
                    # Multiple addons modify same entity - merge them intelligently
                    # Keep the original identifier (don't rename when merging)
                    merged_entity = {}
                    for entity_file in entity_list:
                        # Merge data from each addon
                        self._merge_json_data(merged_entity, entity_file['data'])
                    # Ensure the merged entity keeps the original identifier
                    if 'minecraft:client_entity' in merged_entity:
                        if 'description' not in merged_entity['minecraft:client_entity']:
                            merged_entity['minecraft:client_entity']['description'] = {}
                        desc = merged_entity['minecraft:client_entity']['description']
                        desc['identifier'] = entity_id
                        # Sanitize geometry/textures/materials: remove empty-string keys or values
                        # that can appear after merging and produce Molang 'geometry.default not found'
                        for _alias_key in ('geometry', 'textures', 'materials'):
                            if _alias_key in desc and isinstance(desc[_alias_key], dict):
                                desc[_alias_key] = {
                                    k: v for k, v in desc[_alias_key].items()
                                    if k and v and str(k).strip() and str(v).strip()
                                }
                    # Use the first file's path as the output path
                    output_path = entity_list[0]['file_path']
                    _output_zip.writestr(output_path, _json.dumps(merged_entity, indent=2))
                else:
                    # Only one addon modifies this entity
                    # Check if identifier needs renaming (different entity with same identifier)
                    entity_file = entity_list[0]
                    final_data = entity_file['data']
                    # Only rename if IdentifierManager says to (for different entities with same ID)
                    if identifier_manager and identifier_manager.should_rename_identifier(entity_file['original_id']):
                        final_data = identifier_manager.update_json_identifiers(final_data, entity_file['pack_path'])
                    _output_zip.writestr(entity_file['file_path'], _json.dumps(final_data, indent=2))
        
        # Behavior packs (entities folder)
        with _zipfile.ZipFile(_output_zip_path_behavior, 'a') as _output_zip:
            for entity_id, entity_list in _entity_files_by_identifier_behavior.items():
                if len(entity_list) > 1:
                    # Multiple addons modify same entity — use component-group routing for conflicts
                    merged_entity = self._merge_behavior_entity(entity_list)
                    # Ensure the merged entity keeps the original identifier
                    if 'minecraft:entity' in merged_entity:
                        if 'description' not in merged_entity['minecraft:entity']:
                            merged_entity['minecraft:entity']['description'] = {}
                        merged_entity['minecraft:entity']['description']['identifier'] = entity_id
                    output_path = entity_list[0]['file_path']
                    _output_zip.writestr(output_path, _json.dumps(merged_entity, indent=2))
                else:
                    entity_file = entity_list[0]
                    final_data = entity_file['data']
                    if identifier_manager and identifier_manager.should_rename_identifier(entity_file['original_id']):
                        final_data = identifier_manager.update_json_identifiers(final_data, entity_file['pack_path'])
                    _output_zip.writestr(entity_file['file_path'], _json.dumps(final_data, indent=2))
        
        # Merge item files by identifier
        with _zipfile.ZipFile(_output_zip_path_behavior, 'a') as _output_zip:
            for item_id, item_list in _item_files_by_identifier.items():
                if len(item_list) > 1:
                    # Multiple addons modify same item - merge them, keep original identifier
                    merged_item = {}
                    for item_file in item_list:
                        self._merge_json_data(merged_item, item_file['data'])
                    if 'minecraft:item' in merged_item:
                        if 'description' not in merged_item['minecraft:item']:
                            merged_item['minecraft:item']['description'] = {}
                        merged_item['minecraft:item']['description']['identifier'] = item_id
                    output_path = item_list[0]['file_path']
                    _output_zip.writestr(output_path, _json.dumps(merged_item, indent=2))
                else:
                    item_file = item_list[0]
                    final_data = item_file['data']
                    if identifier_manager and identifier_manager.should_rename_identifier(item_file['original_id']):
                        final_data = identifier_manager.update_json_identifiers(final_data, item_file['pack_path'])
                    _output_zip.writestr(item_file['file_path'], _json.dumps(final_data, indent=2))
        
        # Merge block files by identifier
        with _zipfile.ZipFile(_output_zip_path_behavior, 'a') as _output_zip:
            for block_id, block_list in _block_files_by_identifier.items():
                if len(block_list) > 1:
                    # Multiple addons modify same block - merge them, keep original identifier
                    merged_block = {}
                    for block_file in block_list:
                        self._merge_json_data(merged_block, block_file['data'])
                    if 'minecraft:block' in merged_block:
                        if 'description' not in merged_block['minecraft:block']:
                            merged_block['minecraft:block']['description'] = {}
                        merged_block['minecraft:block']['description']['identifier'] = block_id
                    output_path = block_list[0]['file_path']
                    _output_zip.writestr(output_path, _json.dumps(merged_block, indent=2))
                else:
                    block_file = block_list[0]
                    final_data = block_file['data']
                    if identifier_manager and identifier_manager.should_rename_identifier(block_file['original_id']):
                        final_data = identifier_manager.update_json_identifiers(final_data, block_file['pack_path'])
                    _output_zip.writestr(block_file['file_path'], _json.dumps(final_data, indent=2))

        # Merge other JSON, .lang, .material, and .mcfunction files
        self._merge_and_write_files(_json_contents_resource, _output_zip_path_resource)
        self._merge_and_write_files(_json_contents_behavior, _output_zip_path_behavior)
        self._merge_and_write_lang_files(_lang_contents_resource, _output_zip_path_resource)
        self._merge_and_write_lang_files(_lang_contents_behavior, _output_zip_path_behavior)
        self._merge_and_write_material_files(_material_contents, _output_zip_path_resource)
        self._merge_and_write_mcfunction_files(_mcfunction_contents, _output_zip_path_behavior)

        self._remove_empty_files(_output_zip_path_resource)
        self._remove_empty_files(_output_zip_path_behavior)
