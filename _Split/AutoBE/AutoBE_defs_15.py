class AutoBEApp:

    def _merge_behavior_entity(self, entity_list):
        """
        Merge multiple behavior-pack definitions of the same entity.

        Strategy for root `components` conflicts:
          - First addon's value is kept as the base.
          - Each subsequent addon's *conflicting* component is placed into a uniquely-named
            component_group (`autobe_<packname>_ov`) and that group is activated via the
            `minecraft:entity_spawned` event.  This means ALL addons' component values are
            present in the file and Bedrock applies them in component-group stack order —
            fully deterministic, no silent drops.
          - Non-conflicting components are merged into the base directly.
        Everything outside `components` (component_groups, events, description, animations,
        scripts, …) is union-merged as usual.
        """
        if not entity_list:
            return {}
        if len(entity_list) == 1:
            return entity_list[0]['data']

        merged = {}
        self._merge_json_data(merged, entity_list[0]['data'])

        for entity_file in entity_list[1:]:
            src = entity_file['data']
            pack_raw = _os.path.basename(entity_file['pack_path'])
            pack_raw = _re.sub(r'\.(mcpack|mcaddon)$', '', pack_raw, flags=_re.IGNORECASE)
            pack_raw = _re.sub(r'_modified$', '', pack_raw, flags=_re.IGNORECASE)
            pack_raw = _re.sub(r'_\d+$', '', pack_raw)
            clean = _re.sub(r'[^a-zA-Z0-9]', '_', pack_raw)[:16].strip('_')
            group_name = f"autobe_{clean}_ov"

            ent_key = 'minecraft:entity'
            if ent_key not in src or ent_key not in merged:
                self._merge_json_data(merged, src)
                continue

            src_def = src[ent_key]
            base_def = merged[ent_key]
            src_comps = src_def.get('components', {})
            base_comps = base_def.setdefault('components', {})

            overrides = {}
            for comp_key, comp_val in src_comps.items():
                if comp_key in base_comps:
                    if _json.dumps(comp_val, sort_keys=True) != _json.dumps(base_comps[comp_key], sort_keys=True):
                        # Genuinely different value — route to component group
                        overrides[comp_key] = comp_val
                    # else: identical, skip
                else:
                    base_comps[comp_key] = comp_val  # new component, add to base

            if overrides:
                base_def.setdefault('component_groups', {})[group_name] = overrides
                spawn_ev = base_def.setdefault('events', {}).setdefault('minecraft:entity_spawned', {})
                cg_list = spawn_ev.setdefault('add', {}).setdefault('component_groups', [])
                if group_name not in cg_list:
                    cg_list.append(group_name)

            # Merge everything else in the entity definition except components (already handled)
            for k, v in src_def.items():
                if k == 'components':
                    continue
                if k in base_def:
                    if isinstance(base_def[k], dict) and isinstance(v, dict):
                        self._merge_json_data(base_def[k], v)
                    elif isinstance(base_def[k], list) and isinstance(v, list):
                        base_def[k] = self._union_merge_list(base_def[k], v)
                else:
                    base_def[k] = v

            # Merge top-level keys outside minecraft:entity
            for k, v in src.items():
                if k == ent_key:
                    continue
                if k not in merged:
                    merged[k] = v

        return merged

    # Numeric keys where "take the max" is the safest strategy when two addons conflict
    _MERGE_MAX_KEYS = frozenset({
        'value', 'max', 'min', 'amount', 'speed', 'damage',
        'range', 'radius', 'duration', 'cooldown', 'max_dist',
        'priority',  # lower priority number = higher priority; max keeps the less aggressive override
    })
    # Keys whose list values must always be union-deduplicated (order preserved)
    _UNION_LIST_KEYS = frozenset({
        'component_groups', 'animations', 'animate', 'particle_effects',
        'sound_effects', 'scripts', 'pools', 'entries', 'conditions',
        'spawn_rules', 'behaviors', 'render_controllers',
    })

    @staticmethod
    def _union_merge_list(existing, incoming):
        """Return existing + any items from incoming not already present (by JSON fingerprint)."""
        seen = {_json.dumps(i, sort_keys=True) if isinstance(i, (dict, list)) else str(i) for i in existing}
        result = list(existing)
        for item in incoming:
            key = _json.dumps(item, sort_keys=True) if isinstance(item, (dict, list)) else str(item)
            if key not in seen:
                result.append(item)
                seen.add(key)
        return result

    def _merge_json_data(self, target, source):
        """
        Recursively merges JSON data from `source` into `target` with intelligent conflict resolution.
        Handles entity files, player.json, and other common conflict scenarios.
        """
        for key, value in source.items():
            if key not in target:
                target[key] = value
                continue

            t = target[key]

            # Dicts always recurse
            if isinstance(t, dict) and isinstance(value, dict):
                self._merge_json_data(t, value)

            # Lists — union-deduplicate known union keys; extend others
            elif isinstance(t, list) and isinstance(value, list):
                if key in self._UNION_LIST_KEYS:
                    target[key] = self._union_merge_list(t, value)
                else:
                    target[key] = self._union_merge_list(t, value)

            # Primitive vs primitive
            else:
                if key in ('format_version', 'description', 'identifier'):
                    pass  # keep first
                elif key in self._MERGE_MAX_KEYS and isinstance(t, (int, float)) and isinstance(value, (int, float)):
                    # Two addons set the same stat differently — honour both by taking the larger value
                    target[key] = max(t, value)
                else:
                    target[key] = value  # last-wins for everything else

    def _copy_to_zip(self, _pack_zip, _item, _output_zip, _json_data=None, _pack_path=None, _identifier_manager=None, _override_name=None, _written_paths=None):
        _out_name = _override_name if _override_name else _item.filename
        # First-wins for binary assets: skip if this path was already written by an earlier pack
        if _written_paths is not None and _json_data is None:
            if _out_name in _written_paths:
                return
            _written_paths.add(_out_name)
        with _pack_zip.open(_item) as _file_data:
            if _json_data is not None:
                # If identifier manager is provided, update identifiers in JSON data
                if _identifier_manager and _pack_path:
                    try:
                        _json_data = _identifier_manager.update_json_identifiers(_json_data, _pack_path)
                    except Exception as e:
                        _logging.warning(f"Error updating identifiers in {_item.filename}: {e}")
                # ExtendedBE: run per-file fixers on pre-parsed JSON files too.
                # Entity behavior, recipe, sounds.json etc. all arrive here as dicts —
                # fixers never reached them before because they were in the else branch.
                _ebe_on_json = (
                    _EXTENDEDBE_FIXERS and _pack_path and
                    getattr(getattr(self, 'extendedbe_enabled_var', None), 'get', lambda: False)()
                )
                if _ebe_on_json:
                    try:
                        _jb_in = _json.dumps(_json_data, indent=2).encode('utf-8')
                        _ebe_path2, _jb_out = _extendedbe.apply_fixers(
                            _EXTENDEDBE_FIXERS, _os.path.basename(_pack_path), _out_name, _jb_in)
                        if _ebe_path2 != _out_name:
                            _out_name = _ebe_path2
                        if _jb_out != _jb_in:
                            try:
                                _json_data = _json.loads(_jb_out.decode('utf-8'))
                            except Exception:
                                pass
                    except Exception as _ebe_je:
                        _logging.warning(f"[ExtendedBE] JSON fixer error on {_out_name}: {_ebe_je}")
                _output_zip.writestr(_out_name, _json.dumps(_json_data, indent=2))
            else:
                file_data = _file_data.read()
                # ExtendedBE: apply per-addon fixers (broken/outdated addon patches).
                # Only runs when the user has enabled it in Settings → ExtendedBE Addon Fixer.
                _ebe_on = (
                    _EXTENDEDBE_FIXERS and _pack_path and
                    getattr(getattr(self, 'extendedbe_enabled_var', None), 'get', lambda: False)()
                )
                if _ebe_on:
                    try:
                        _pack_basename = _os.path.basename(_pack_path)
                        _ebe_path, file_data = _extendedbe.apply_fixers(
                            _EXTENDEDBE_FIXERS, _pack_basename, _out_name, file_data)
                        if _ebe_path != _out_name:
                            _out_name = _ebe_path  # fixer moved the file to a new path
                    except Exception as _ebe_err:
                        _logging.warning(f"[ExtendedBE] apply_fixers error on {_out_name}: {_ebe_err}")
                # Update identifiers in text-based files (scripts, etc.)
                if _identifier_manager and _pack_path and _out_name.endswith(('.js', '.mcfunction', '.lang')):
                    try:
                        text_content = file_data.decode('utf-8', errors='ignore')
                        updated_text = _identifier_manager.update_text_identifiers(text_content, _pack_path)
                        file_data = updated_text.encode('utf-8')
                    except Exception as e:
                        _logging.warning(f"Error updating identifiers in {_item.filename}: {e}")
                # JS compatibility patches — run unconditionally so they are never
                # silently skipped if the identifier-manager step throws above.
                if _out_name.endswith('.js'):
                    try:
                        js_text = file_data.decode('utf-8', errors='ignore')
                        # Strip bare empty action-bar clears (setActionBar("") / setActionBar(''))
                        # that silence other addons' HUD channels in merged packs.
                        # e.g. SWAILA clears with "" every 10 ticks, wiping MQPS's 'mqps...'
                        # bar data. Bedrock's natural fade + MQPS's next update handle cleanup.
                        js_text = _re.sub(
                            r'(?:[A-Za-z_$][\w$]*\.)+setActionBar\s*\(\s*(?:\'\'|"")\s*\)',
                            '(0)',
                            js_text
                        )
                        # Stagger entity-detecting scripts (SWAILA-like) from 10 → 25 ticks.
                        # MQPS runs every 10 ticks; LCM(10,25)=50 ticks before they align.
                        # SWAILA's setActionBar calls overwrite MQPS's data ~20% of the time
                        # instead of ~50% with 10→11, reducing visible flicker of MQPS bars.
                        if 'getEntitiesFromViewDirection' in js_text:
                            js_text = js_text.replace('}, 10);', '}, 25);')
                        file_data = js_text.encode('utf-8')
                    except Exception as e:
                        _logging.warning(f"Error applying JS compat patches in {_item.filename}: {e}")
                _output_zip.writestr(_out_name, file_data)

    def _handle_json_item(self, _pack_zip, _item, _json_contents, _output_zip, _module_type=None, _pack_path=None, _identifier_manager=None, _override_name=None):
        with _pack_zip.open(_item) as _json_file:
            try:
                _json_data = self._load_json_with_comments(_json_file)
                if isinstance(_json_data, dict):
                    # Update identifiers before storing for merging
                    if _identifier_manager and _pack_path:
                        try:
                            _json_data = _identifier_manager.update_json_identifiers(_json_data, _pack_path)
                        except Exception as e:
                            _logging.warning(f"Error updating identifiers in {_item.filename}: {e}")
                    _json_name = _override_name if _override_name else _item.filename
                    _json_contents.setdefault(_json_name, []).append(_json_data)
                else:
                    # Parser returned None or a non-dict (list, etc.) — fall back to raw copy so
                    # the file is not silently lost. The merged version (if any) is written later
                    # and will be the last entry in the zip, so it takes precedence.
                    self._copy_to_zip(_pack_zip, _item, _output_zip, None, _pack_path, _identifier_manager, _override_name=_override_name)
            except Exception:
                # Catch all parse/decode errors — not just JSONDecodeError — so a file is never
                # silently dropped. Raw copy ensures textures/sounds are still present in output.
                self._copy_to_zip(_pack_zip, _item, _output_zip, None, _pack_path, _identifier_manager, _override_name=_override_name)

    def _merge_and_write_files(self, _json_contents, _output_zip_path):
        for _json_file, _json_list in _json_contents.items():
            _merged_content = self._merge_json(_json_list, _os.path.basename(_json_file))
            with _zipfile.ZipFile(_output_zip_path, 'a') as _output_zip:
                _output_zip.writestr(_json_file, _json.dumps(_merged_content, indent=2))

    def _merge_and_write_lang_files(self, _lang_contents, _output_zip_path):
        for _lang_file, _lang_list in _lang_contents.items():
            _merged_lang_content = self._merge_lang_files(_lang_list)
            with _zipfile.ZipFile(_output_zip_path, 'a') as _output_zip:
                _output_zip.writestr(_lang_file, _merged_lang_content)

    def _merge_and_write_material_files(self, _material_contents, _output_zip_path):
        for _material_file, _material_list in _material_contents.items():
            _merged_material_content = self._merge_json(_material_list, _os.path.basename(_material_file))
            with _zipfile.ZipFile(_output_zip_path, 'a') as _output_zip:
                _output_zip.writestr(_material_file, _json.dumps(_merged_material_content, indent=2))

    def _merge_and_write_mcfunction_files(self, _mcfunction_contents, _output_zip_path):
        for _mcfunction_file, _mcfunction_list in _mcfunction_contents.items():
            _merged_mcfunction_content = "\n".join(strip_bom(x) for x in _mcfunction_list)
            _merged_mcfunction_content = strip_bom(_merged_mcfunction_content)
            with _zipfile.ZipFile(_output_zip_path, 'a') as _output_zip:
                _output_zip.writestr(_mcfunction_file, _merged_mcfunction_content)

    def _remove_empty_files(self, _zip_path):
        with _zipfile.ZipFile(_zip_path, 'r') as _zip:
            file_list = _zip.infolist()
            temp_file_path = _zip_path + ".temp"
            with _zipfile.ZipFile(temp_file_path, 'w') as temp_zip:
                for file in file_list:
                    if file.file_size > 0:
                        temp_zip.writestr(file, _zip.read(file.filename))

        _os.remove(_zip_path)
        _os.rename(temp_file_path, _zip_path)

    def _validate_pack_zip(self, _zip_path, _pack_kind):
        report = {
            "pack_kind": _pack_kind,
            "zip_path": _os.path.abspath(_zip_path),
            "exists": _os.path.exists(_zip_path),
            "leaked_prefix_paths": [],
            "has_manifest": False,
            "texts": {
                "has_en_us_lang": False,
                "has_en_us_json": False,
                "has_languages_json": False,
                "has_language_names_json": False,
            },
        }

        if not report["exists"]:
            return report

        try:
            with _zipfile.ZipFile(_zip_path, 'r') as zf:
                names = zf.namelist()
                report["has_manifest"] = any(n.lower().endswith('manifest.json') and '/' not in n.strip('/') for n in names)
                report["leaked_prefix_paths"] = [n for n in names if n.startswith('R/') or n.startswith('B/')]

                if _pack_kind == "resource":
                    report["texts"]["has_en_us_lang"] = any(n.lower() == 'texts/en_us.lang' for n in names)
                    report["texts"]["has_en_us_json"] = any(n.lower() == 'texts/en_us.json' for n in names)
                    report["texts"]["has_languages_json"] = any(n.lower() == 'texts/languages.json' for n in names)
                    report["texts"]["has_language_names_json"] = any(n.lower() == 'texts/language_names.json' for n in names)
        except Exception as e:
            report["error"] = str(e)

        return report

    def _write_merge_report(self, _output_dir, _bp_path, _rp_path, _source_packs):
        try:
            report = {
                "output_dir": _os.path.abspath(_output_dir),
                "source_packs": [_os.path.abspath(p) for p in _source_packs],
                "behavior_pack": self._validate_pack_zip(_bp_path, "behavior"),
                "resource_pack": self._validate_pack_zip(_rp_path, "resource"),
            }
            report_path = _os.path.join(_output_dir, "_autobe_merge_report.json")
            with open(report_path, 'w', encoding='utf-8') as f:
                _json.dump(report, f, indent=2)
        except Exception as e:
            _logging.warning(f"Could not write merge report: {e}")
    
    def _process_files(self, _selected_files):
        _imported_files = []

        _scripts_path = _os.path.join(self._out_dir, "scripts")

        # Ensure the scripts directory is empty or create it if it doesn't exist
        if _os.path.exists(_scripts_path):
            _shutil.rmtree(_scripts_path)
        _os.makedirs(_scripts_path, exist_ok=True)

        _main_js_path = _os.path.join(_scripts_path, "CodeNex.js")

        # Each pack gets its own isolated subdirectory under scripts/{pack_num}/
        # so that utility modules (utils.js, types.js, etc.) from different packs can
        # never overwrite each other.  Only the manifest entry file is renamed within
        # that directory; all other files keep their original names and relative imports
        # continue to resolve correctly because they share the same subdirectory.
        # _pack_info maps: mcpack_path -> (renamed_dict, pack_dir_path)
        _pack_info = {}

        for _mcpack_file in _selected_files:
            _pack_num  = _random.randint(10000, 99999)
            _pack_dir  = _os.path.join(_scripts_path, str(_pack_num))
            _renamed_in_pack = {}

            try:
                with _zipfile.ZipFile(_mcpack_file, 'r') as _zip_ref:
                    _namelist = _zip_ref.namelist()

                    # Collect script items from the two supported layouts
                    _script_items   = [n for n in _namelist
                                       if n.startswith('scripts/') and not n.endswith('/')]
                    _b_script_items = [n for n in _namelist
                                       if n.startswith('B/scripts/') and not n.endswith('/')]
                    _logging.info(f"[_process_files] {_os.path.basename(_mcpack_file)}: found {len(_script_items)} scripts, {len(_b_script_items)} B/scripts")

                    # Extract every script into this pack's isolated subdirectory,
                    # stripping the leading 'scripts/' (or 'B/scripts/') prefix.
                    # Apply JS compatibility patches (setActionBar stripping, tick stagger).
                    if _script_items or _b_script_items:
                        _os.makedirs(_pack_dir, exist_ok=True)
                        for _item in _script_items:
                            _rel = _item[len('scripts/'):]
                            if _rel:
                                _dest = _os.path.join(_pack_dir, _rel)
                                _os.makedirs(_os.path.dirname(_dest), exist_ok=True)
                                _js_bytes = _zip_ref.read(_item)
                                # Apply JS compatibility patches to any script
                                if _rel.endswith('.js'):
                                    _js_text = _js_bytes.decode('utf-8', errors='ignore')
                                    # Fix 1: Strip empty setActionBar calls (prevents wiping other addons' data)
                                    _js_text = __import__('re').sub(
                                        r'(?:[A-Za-z_$][\w$]*\.)+setActionBar\s*\(\s*(?:\'\'|"")\s*\)',
                                        '(0)',
                                        _js_text
                                    )
                                    # Detect if this script is an actionbar-heavy addon
                                    _uses_actionbar = 'setActionBar' in _js_text
                                    _is_mqps = 'mqps' in _js_text.lower() or 'more_hunger_bar' in _js_text
                                    _has_timer = any(x in _js_text for x in ['runInterval', 'setInterval', 'setTimeout', 'runTimeout'])
                                    
                                    # Fix 2: Stagger ANY timed actionbar script to reduce collisions
                                    if _uses_actionbar and _has_timer and '}, 10);' in _js_text:
                                        _js_text = _js_text.replace('}, 10);', '}, 25);')
                                    
                                    # Fix 3: Keep SWAILA on actionbar - MQPS visibility handles collision
                                    # No need to move to title channel as subtitle doesn't work properly
                                    _js_bytes = _js_text.encode('utf-8')
                                with open(_dest, 'wb') as _dst:
                                    _dst.write(_js_bytes)
                        for _item in _b_script_items:
                            _rel = _item[len('B/scripts/'):]
                            if _rel:
                                _dest = _os.path.join(_pack_dir, _rel)
                                _os.makedirs(_os.path.dirname(_dest), exist_ok=True)
                                _js_bytes = _zip_ref.read(_item)
                                # Apply JS compatibility patches to any script
                                if _rel.endswith('.js'):
                                    _js_text = _js_bytes.decode('utf-8', errors='ignore')
                                    # Fix 1: Strip empty setActionBar calls (prevents wiping other addons' data)
                                    _js_text = __import__('re').sub(
                                        r'(?:[A-Za-z_$][\w$]*\.)+setActionBar\s*\(\s*(?:\'\'|"")\s*\)',
                                        '(0)',
                                        _js_text
                                    )
                                    # Detect if this script is an actionbar-heavy addon
                                    _uses_actionbar = 'setActionBar' in _js_text
                                    _is_mqps = 'mqps' in _js_text.lower() or 'more_hunger_bar' in _js_text
                                    _has_timer = any(x in _js_text for x in ['runInterval', 'setInterval', 'setTimeout', 'runTimeout'])
                                    
                                    # Fix 2: Stagger ANY timed actionbar script to reduce collisions
                                    if _uses_actionbar and _has_timer and '}, 10);' in _js_text:
                                        _js_text = _js_text.replace('}, 10);', '}, 25);')
                                    
                                    # Fix 3: Keep SWAILA on actionbar - MQPS visibility handles collision
                                    # No need to move to title channel as subtitle doesn't work properly
                                    _js_bytes = _js_text.encode('utf-8')
                                with open(_dest, 'wb') as _dst:
                                    _dst.write(_js_bytes)

                    try:
                        _manifest_json = self._get_manifest_data(_mcpack_file)
                        if _manifest_json is None:
                            raise ValueError("Failed to parse manifest.json")
                    except KeyError:
                        log_error(KeyError)
                        _messagebox.showerror("Error", f"manifest.json not found in {_os.path.basename(_mcpack_file)}")
                        continue
                    except Exception as _e:
                        log_error(_e)
                        _messagebox.showerror("Error", f"Error reading manifest.json in {_os.path.basename(_mcpack_file)}: {str(_e)}")
                        continue

                    _entries = [_m.get("entry") for _m in _manifest_json.get("modules", []) if "entry" in _m]

                    for _entry in _entries:
                        if not _entry:
                            continue
                        try:
                            # Strip the leading 'scripts/' prefix from the entry path so we
                            # can locate the file inside the pack's isolated subdirectory.
                            _entry_rel      = _entry[len('scripts/'):] if _entry.startswith('scripts/') else _entry
                            _entry_basename = _os.path.basename(_entry_rel)
                            _new_name       = f"{_pack_num}_{_entry_basename}"

                            _old_path = _os.path.join(_pack_dir, _entry_rel)
                            _new_path = _os.path.join(_os.path.dirname(_old_path), _new_name)

                            # Fallback: entry declared without a subdir (e.g. "main.js")
                            if not _os.path.exists(_old_path):
                                _flat = _os.path.join(_pack_dir, _entry_basename)
                                if _os.path.exists(_flat):
                                    _old_path = _flat
                                    _new_path = _os.path.join(_pack_dir, _new_name)

                            if _os.path.exists(_old_path):
                                _os.rename(_old_path, _new_path)
                                _renamed_in_pack[_entry_basename] = _new_name
                                _imported_files.append(_new_path)
                            else:
                                _imported_files.append(_old_path)

                        except Exception as _e:
                            log_error(_e)
                            _messagebox.showerror("Error", f"Error processing entry {_entry} in {_os.path.basename(_mcpack_file)}: {str(_e)}")
                            continue

            except Exception as _e:
                log_error(_e)
                _messagebox.showerror("Error", f"Failed to process {_os.path.basename(_mcpack_file)}: {str(_e)}")

            _pack_info[_mcpack_file] = (_renamed_in_pack, _pack_dir)

        # ── Fix JS import paths before rename rewriting ──────────────────────
        # Two classes of import break when scripts move into an isolated subdir:
        #
        # 1. Bare module imports (import 'name' / import 'name.js') that relied on
        #    Bedrock resolving from the scripts/ root.  After isolation the file is
        #    in scripts/{uuid}/name.js but 'name' still resolves from scripts/ root
        #    which no longer has it.  Convert to './name' when the target file
        #    exists alongside the importing file.
        #
        # 2. Relative imports whose ../ count exceeds the file's nesting depth
        #    within the pack subdir.  Bedrock clamps resolution at the scripts/
        #    root, so 'scripts/a/b/c/file.js' with '../../../../x' resolves to
        #    'scripts/x'.  After isolation, the same file is at
        #    'scripts/{uuid}/a/b/c/file.js' (depth 4) and the same ../../../../
        #    resolves to 'scripts/x' — but the file is now 'scripts/{uuid}/x'.
        #    Cap excessive ../ to the file's actual depth within the pack dir so
        #    the import resolves to the correct location inside {uuid}/.
        for _mcpack_file, (_renamed_in_pack, _pack_dir) in _pack_info.items():
            if not _os.path.isdir(_pack_dir):
                continue
            _pack_dir_p = _pathlib.Path(_pack_dir)
            for _js_root, _, _js_files in _os.walk(_pack_dir):
                for _js_fname in _js_files:
                    if not _js_fname.endswith('.js'):
                        continue
                    _jfp = _os.path.join(_js_root, _js_fname)
                    try:
                        _jfp_p   = _pathlib.Path(_jfp)
                        _jfp_rel = _jfp_p.relative_to(_pack_dir_p)
                        _depth   = len(_jfp_rel.parent.parts)  # dirs deep from pack_dir
                        _jdir    = _jfp_p.parent

                        with open(_jfp, 'r', encoding='latin-1') as _jf:
                            _jcontent = _jf.read()
                        _joriginal = _jcontent

                        # ── 1. bare imports → ./relative ──────────────────────
                        def _fix_bare(m):
                            _pfx   = m.group(1)   # 'import' or 'from'
                            _q     = m.group(2)   # quote char
                            _spec  = m.group(3)   # the specifier
                            # Skip if already relative or a Bedrock built-in
                            if _spec.startswith(('.', '/', '@')) or not _spec:
                                return m.group(0)
                            # Try with and without .js extension
                            _bare_name = _spec if _spec.endswith('.js') else _spec + '.js'
                            _candidate = _jdir / _bare_name
                            if _candidate.exists():
                                return f'{_pfx} {_q}./{_spec}{_q}'
                            _candidate2 = _jdir / _spec
                            if _candidate2.exists():
                                return f'{_pfx} {_q}./{_spec}{_q}'
                            return m.group(0)

                        _jcontent = _re.sub(
                            r'\b(import|from)\s+(["\'])([^"\'./\n@][^"\'?\n]*)(\2)',
                            _fix_bare, _jcontent)

                        # ── 2. cap excessive ../ in relative imports ──────────
                        def _cap_dots(m):
                            _pfx  = m.group(1)   # 'import' or 'from'
                            _q    = m.group(2)   # quote char
                            _dots = m.group(3)   # the repeated ../ prefix
                            _rest = m.group(4)   # remainder of the path
                            _n    = _dots.count('../')
                            if _n <= _depth:
                                return m.group(0)
                            _capped = '../' * _depth
                            return f'{_pfx} {_q}{_capped}{_rest}{_q}'

                        _jcontent = _re.sub(
                            r'\b(import|from)\s+(["\'])((?:\.\./){2,})([^"\'?\n]+)(\2)',
                            _cap_dots, _jcontent)

                        # ── 3. self-rescheduling form delay fix ───────────────
                        # Addons like BetterCombat show a persistent ActionFormData that
                        # re-queues itself every N ticks via system.runTimeout inside a
                        # finally block.  When N is tiny (e.g. 20 ticks = 1 second) the
                        # form re-appears immediately after dismissal, covering the HUD
                        # and preventing title-based UI addons (e.g. Water Temperature
                        # System) from ever displaying their overlays.
                        # Raise the INITIAL declaration value to 600 ticks (30 s) while
                        # leaving any in-function reassignments (e.g. nextShowDelay = 0
                        # on button press) untouched so the toggle button still works.
                        if ('nextShowDelay' in _jcontent
                                and '.show(' in _jcontent
                                and 'runTimeout' in _jcontent):
                            def _fix_show_delay(m):
                                _val = int(m.group(1))
                                if _val < 100:
                                    return f'let nextShowDelay = 600'
                                return m.group(0)
                            _jcontent = _re.sub(
                                r'\blet\s+nextShowDelay\s*=\s*(\d+)',
                                _fix_show_delay, _jcontent)

                        # ── 4. setTitle() UI-binding prefix → add stayDuration ─
                        # The Water Temperature System (and similar addons) send titles
                        # whose text starts with special §-code sequences that the RP's
                        # hud_screen.json patches intercept and hide, replacing them with
                        # custom HUD elements (thermometer, thirst bar).  Without an
                        # explicit stayDuration the default ~3.5 s title window expires
                        # between thirst-floor-change events, making the custom HUD
                        # disappear.  Append TitleDisplayOptions to bare setTitle()
                        # calls whose argument string begins with multiple §-codes
                        # (\\u00A7 escape or latin-1 0xA7 byte) so they stay 10 s.
                        if '.setTitle(' in _jcontent:
                            # Match: .setTitle(TEMP_KEYS[level]);
                            _jcontent = _re.sub(
                                r'(\.setTitle\(TEMP_KEYS\[level\])\)',
                                r'\1, {fadeInDuration:0,stayDuration:200,fadeOutDuration:0})',
                                _jcontent)
                            # Match single-line: .setTitle("§§§§§§§§..." + expr);
                            _jcontent = _re.sub(
                                r'(\.setTitle\("(?:\\u00A7[a-zA-Z0-9]){3,}[^"]*"[^;{]*?)\)',
                                r'\1, {fadeInDuration:0,stayDuration:200,fadeOutDuration:0})',
                                _jcontent)
                            # Match multi-line thirst setTitle block (no existing 2nd arg)
                            # Pattern: .setTitle(\r?\n  "§§§..."  + expr\r?\n  );
                            # Use lambda to preserve original CRLF/LF style;
                            # [^;\r\n]* excludes \r so it is not swallowed into group 2
                            _nl = '\r\n' if '\r\n' in _jcontent else '\n'
                            def _fix_ml_title(m):
                                return (m.group(1) + _nl
                                        + m.group(2) + ','
                                        + _nl + m.group(3)
                                        + '{fadeInDuration:0,stayDuration:200,fadeOutDuration:0}'
                                        + _nl + m.group(3) + ');')
                            _jcontent = _re.sub(
                                r'(\.setTitle\()\s*\r?\n(\s*"(?:\\u00A7[a-zA-Z0-9]){3,}[^"\r\n]*"[^;\r\n]*)\r?\n(\s*)\);',
                                _fix_ml_title,
                                _jcontent)

                        # ── 5. :icon: shortcode → JS Unicode escape ───────────
                        # Some addons embed :heart: or :craftable_toggle_on:
                        # as literal ASCII placeholders, expecting them to
                        # render as Minecraft UI icons.  Replace with JS
                        # \uXXXX escapes so they render in Minecraft's font.
                        _SHORTCODE_MAP = {
                            ':heart:':               r'\u2764',  # ❤
                            ':heart_outline:':       r'\u2661',  # ♡
                            ':craftable_toggle_on:': r'\u2611',  # ☑
                            ':craftable_toggle_off:':r'\u2610',  # ☐
                            ':star:':                r'\u2605',  # ★
                            ':star_empty:':          r'\u2606',  # ☆
                        }
                        for _sc, _esc in _SHORTCODE_MAP.items():
                            if _sc in _jcontent:
                                _jcontent = _jcontent.replace(_sc, _esc)

                        # ── 6. entityHurt damagingEntity null-safety ──────────
                        # damagingEntity can be undefined for environmental
                        # damage (fall, fire, void). Using attacker.getComponent()
                        # without a null guard throws TypeError every time.
                        # Replace with optional chaining so the callback silently
                        # returns undefined instead of crashing.
                        if 'damagingEntity' in _jcontent and '.getComponent(' in _jcontent:
                            # Covers both renamed patterns: attacker.getComponent, source.getComponent
                            _jcontent = _re.sub(
                                r'\b(attacker|damagingEntity)\b\.getComponent\(',
                                r'\1?.getComponent(',
                                _jcontent)
                            _jcontent = _re.sub(
                                r'\b(attacker|damagingEntity)\b\.getComponent\(([^)]+)\)\.getEquipment\(',
                                r'\1?.getComponent(\2)?.getEquipment(',
                                _jcontent)

                        # ── 7. playerInteractWithBlock data.source → data.player ─
                        # Bedrock's PlayerInteractWithBlockBeforeEvent exposes
                        # .player, not .source.  Older packs use data.source which
                        # is undefined in current engine versions → TypeError.
                        # Replace with a safe fallback that works on both old and
                        # new API versions.
                        if 'playerInteractWithBlock' in _jcontent and 'data.source' in _jcontent:
                            _jcontent = _jcontent.replace(
                                'data.source.name',
                                '(data.source??data.player)?.name')
                            _jcontent = _jcontent.replace(
                                'data.source.dimension',
                                '(data.source??data.player)?.dimension')
                            # Guard the canonical assignment used by older packs:
                            #   const player = data.source;
                            # Use a tightly-scoped regex anchored to declaration
                            # keywords so comparison operators (===, !==) are
                            # never accidentally matched.
                            _jcontent = _re.sub(
                                r'\b(const|let|var)\s+(\w+)\s*=\s*data\.source\s*;',
                                r'\1 \2 = (data.source??data.player);',
                                _jcontent)

                        if _jcontent != _joriginal:
                            with open(_jfp, 'w', encoding='latin-1') as _jf:
                                _jf.write(_jcontent)
                    except Exception:
                        pass

        # Update import references and apply namespacing within each pack's isolated
        # directory only — prevents cross-pack import rewrites from corrupting unrelated scripts.
        for _mcpack_file, (_renamed_in_pack, _pack_dir) in _pack_info.items():
            if not _renamed_in_pack or not _os.path.isdir(_pack_dir):
                continue

            for _root, _, _files in _os.walk(_pack_dir):
                for _file in _files:
                    if not _file.endswith('.js'):
                        continue
                    try:
                        _file_path = _os.path.join(_root, _file)
                        with open(_file_path, 'r', encoding='latin-1') as _js_file:
                            _content = _js_file.read()

                        for _old_name, _new_name in _renamed_in_pack.items():
                            _old_wo_ext = _old_name.rsplit('.', 1)[0]
                            _new_wo_ext = _new_name.rsplit('.', 1)[0]
                            _pat_ext    = rf"(?<=['\"/]){_re.escape(_old_name)}(?=['\";])"
                            _pat_no_ext = rf"(?<=['\"/]){_re.escape(_old_wo_ext)}(?=['\";])"
                            _content = _re.sub(_pat_ext,    _new_name,    _content)
                            _content = _re.sub(_pat_no_ext, _new_wo_ext,  _content)

                        with open(_file_path, 'w', encoding='latin-1') as _js_file:
                            _js_file.write(_content)
                    except Exception as _e:
                        log_error(_e)
                        _messagebox.showerror("Error", f"Error updating import statements in {_file}: {str(_e)}")
                        continue

            # Namespace dynamic property keys and scoreboard objective names per pack
            # so scripts that shared a pack UUID before merging don't collide in the
            # combined pack's single UUID namespace.
            try:
                self._namespace_script_properties(_pack_dir, _mcpack_file, _renamed_in_pack)
            except Exception:
                pass

        _valid_imports = [f for f in _imported_files if _os.path.exists(f)]
        _logging.info(f"[_process_files] {len(_valid_imports)} entry files found across all packs -> writing CodeNex.js")
        for _dbg in _valid_imports:
            _logging.info(f"  import: {_os.path.relpath(_dbg, _scripts_path).replace(chr(92), '/')}")

        # Write imports to CodeNex.js only if the files exist.
        # Static imports MUST be used here — Bedrock resolves all static imports
        # synchronously before the first game tick runs. Dynamic imports (await import())
        # are async and cause top-level event subscriptions (world.afterEvents.playerSpawn
        # etc.) to miss the first tick, breaking spawn-item and UI addons like Lorewarden.
        with open(_main_js_path, 'w', encoding='utf-8') as _main_js_file:
            _main_js_file.write('// AutoBE merged script bridge — generated by CodeNex\n')
            _main_js_file.write('// Each pack script is imported once; dynamic property keys and\n')
            _main_js_file.write('// scoreboard objective names are auto-namespaced to prevent collisions.\n\n')
            _main_js_file.write(f'// {len(_imported_files)} pack(s) with scripts detected\n')
            _main_js_file.write('console.warn("[AutoBE CodeNex] Script bridge loading...");\n\n')
            for _imported_file in _imported_files:
                if _os.path.exists(_imported_file):
                    try:
                        _file_name = _os.path.relpath(_imported_file, _scripts_path).replace("\\", "/")
                        _main_js_file.write(f'import "./{_file_name}";\n')
                    except Exception as _e:
                        log_error(_e)
                        _messagebox.showerror("Error", f"Error writing to CodeNex.js for {_imported_file}: {str(_e)}")
                        continue

        # Append a startup-complete marker so the content log confirms all imports ran.
        try:
            with open(_main_js_path, 'a', encoding='utf-8') as _main_js_file:
                _main_js_file.write(f'\nconsole.warn("[AutoBE CodeNex] All {len(_imported_files)} pack script(s) loaded.");\n')
        except Exception:
            pass

        # Strip any stale bare-name imports that were never renamed (legacy safety net).
        try:
            with open(_main_js_path, 'r') as _main_js_file:
                _main_js_content = _main_js_file.read()

            _main_js_content = _main_js_content.replace('import "./main.js";', '')
            _main_js_content = _main_js_content.replace('import "./Main.js";', '')

            with open(_main_js_path, 'w', encoding='utf-8') as _main_js_file:
                _main_js_file.write(_main_js_content)
        except Exception as _e:
            log_error(_e)
            _messagebox.showerror("Error", f"Error finalizing CodeNex.js: {str(_e)}")
    
    # ──────────────────────────────────────────────────────────────────────────

    # (Player Body Shapes feature removed)
    _PLACEHOLDER_PBS = None  # kept for settings compatibility; feature is disabled
    def _scan_script_runtime_conflicts(self, selected_files):
        """
        Scan every JS script in every selected pack for direct runtime entity/world
        property writes.  Returns a dict:
            {(component_or_obj, property_name): [(pack_display_name, file_path, line_no), ...]}
        Only entries with 2+ packs are genuine conflicts.  Runs fast (regex only, no AST).
        """
        # Patterns that indicate a direct runtime property write — covers the most common cases
        _WRITE_PATTERNS = [
            # entity.getComponent("minecraft:health").currentValue = ...
            (_re.compile(r'getComponent\s*\(\s*["\']([^"\']+)["\']\s*\)\s*\.\s*(\w+)\s*=(?!=)', _re.IGNORECASE), 1, 2),
            # entity.nameTag = ...  / entity.isSneaking = ...  / entity.selectedSlot = ...
            (_re.compile(r'\bentity\s*\.\s*(nameTag|selectedSlot|isSneaking|isFlying|isClimbing|isGliding)\s*=(?!=)', _re.IGNORECASE), None, 1),
            # player.nameTag = ...  etc.
            (_re.compile(r'\bplayer\s*\.\s*(nameTag|selectedSlot|isSneaking|isFlying)\s*=(?!=)', _re.IGNORECASE), None, 1),
            # world.setDynamicProperty (bare, no colon) — already namespaced, but catch remaining bare ones
            # entity.applyKnockback / teleport / kill — can conflict if both call them
            (_re.compile(r'\bentity\s*\.\s*(applyKnockback|teleport|kill|triggerEvent)\s*\(', _re.IGNORECASE), None, 1),
        ]

        # {(comp_or_obj, prop): [(pack_name, file_path, line_no), ...]}
        results = {}

        for pack_path in selected_files:
            pack_display = _os.path.basename(pack_path)
            pack_display = _re.sub(r'\.(mcpack|mcaddon)$', '', pack_display, flags=_re.IGNORECASE)
            pack_display = _re.sub(r'_modified$', '', pack_display, flags=_re.IGNORECASE)

            try:
                with _zipfile.ZipFile(pack_path, 'r') as zf:
                    js_items = [n for n in zf.namelist() if n.endswith('.js')]
                    for js_item in js_items:
                        try:
                            raw = zf.read(js_item).decode('latin-1')
                        except Exception:
                            continue
                        for lineno, line in enumerate(raw.splitlines(), 1):
                            for pattern, comp_group, prop_group in _WRITE_PATTERNS:
                                for m in pattern.finditer(line):
                                    comp = m.group(comp_group) if comp_group else 'entity'
                                    prop = m.group(prop_group)
                                    key = (comp, prop)
                                    bucket = results.setdefault(key, [])
                                    # Only add this pack once per (comp, prop)
                                    if not any(p == pack_display for p, _, _ in bucket):
                                        bucket.append((pack_display, js_item, lineno))
            except Exception:
                continue

        # Keep only entries where 2+ different packs hit the same (comp, prop)
        return {k: v for k, v in results.items() if len(v) >= 2}

    @staticmethod
    def _make_pack_ns(pack_path):
        """Derive a short stable namespace token from a pack filename."""
        name = _os.path.basename(pack_path)
        name = _re.sub(r'\.(mcpack|mcaddon)$', '', name, flags=_re.IGNORECASE)
        name = _re.sub(r'_modified$', '', name, flags=_re.IGNORECASE)
        name = _re.sub(r'_\d+$', '', name)
        ns = _re.sub(r'[^a-z0-9]', '', name.lower())[:8]
        return ns or 'pack'

    def _namespace_script_properties(self, scripts_path, pack_path, renamed_files_in_pack):
        """
        After merging, all scripts share one behavior-pack UUID, so dynamic property
        keys and scoreboard objective names that were previously isolated per-pack UUID
        now collide.  This pass prefixes every bare key with a short pack token so each
        pack's data stays isolated while remaining internally self-consistent.

        Transforms (per-pack, consistent):
          setDynamicProperty("score", v)  →  setDynamicProperty("ns:score", v)
          getDynamicProperty("score")     →  getDynamicProperty("ns:score")
          addObjective("kills", ...)      →  addObjective("ns_kills", ...)
          getObjective("kills")           →  getObjective("ns_kills")
        Keys/names that already contain ':' or look pre-namespaced are left alone.
        """
        ns = self._make_pack_ns(pack_path)

        for root, _, files in _os.walk(scripts_path):
            for fname in files:
                if not fname.endswith('.js'):
                    continue
                fpath = _os.path.join(root, fname)
                try:
                    with open(fpath, 'r', encoding='latin-1') as f:
                        content = f.read()
                    original = content

                    # --- Dynamic properties: prefix bare keys (no colon) ---
                    def _prefix_dynprop(m):
                        key = m.group(2)
                        if ':' in key:
                            return m.group(0)
                        return m.group(1) + ns + ':' + key + m.group(3)

                    content = _re.sub(
                        r'((?:set|get)DynamicProperty\s*\(\s*["\'])([^"\':\n]+)(["\'])',
                        _prefix_dynprop, content)

                    # --- Scoreboard objectives: prefix names (max 16 chars total) ---
                    short_ns = ns[:4]  # 4 chars + '_' + 11 chars = 16

                    def _prefix_obj(m):
                        method = m.group(1)
                        q = m.group(2)
                        name = m.group(3)
                        # Skip if already looks prefixed (contains _)
                        if '_' in name and name.index('_') <= 5:
                            return m.group(0)
                        new_name = (short_ns + '_' + name)[:16]
                        return method + q + new_name + q

                    content = _re.sub(
                        r'((?:add|get|remove)Objective\s*\(\s*)(["\'])([^"\']{1,16})\2',
                        _prefix_obj, content)

                    if content != original:
                        with open(fpath, 'w', encoding='latin-1') as f:
                            f.write(content)
                except Exception:
                    pass

    def _extract_feature_rules(self, _pack_zip, _item, _folder_name, _output_zip):
        with _pack_zip.open(_item) as _file_data:
            _output_zip.writestr(_os.path.join(_folder_name, _os.path.basename(_item.filename)), _file_data.read())
    
    def _merge_entity_json_simple(self, _json_list, _file_name):
        """Simple union merge for entity JSON files to preserve all custom features."""
        if not _json_list:
            return {}
        if len(_json_list) == 1:
            return _json_list[0]
        
        merged = _json.deepcopy(_json_list[0])
        
        for json_obj in _json_list[1:]:
            merged = self._deep_merge_union(merged, json_obj)
        
        return merged
    
    def _deep_merge_union(self, base, overlay):
        """Deep merge with union strategy - overlay adds to base, never overwrites."""
        if not isinstance(base, dict) or not isinstance(overlay, dict):
            return overlay
        
        for key, value in overlay.items():
            if key not in base:
                # Key doesn't exist in base, add it
                base[key] = value
            elif isinstance(base[key], dict) and isinstance(value, dict):
                # Both are dicts, merge recursively
                base[key] = self._deep_merge_union(base[key], value)
            elif isinstance(base[key], list) and isinstance(value, list):
                # Both are lists, concatenate with duplicate removal
                for item in value:
                    if item not in base[key]:
                        base[key].append(item)
            # For primitives, keep base (first wins)
        
        return base
