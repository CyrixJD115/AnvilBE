class AutoBEApp:

    def _unify_cross_group_player_json(self, output_root):
        """Merge all groups' entity/player.json into one comprehensive file and
        write it back to EVERY group's resource_pack.mcpack.

        Bedrock picks the entity/player.json from the single highest-priority RP
        that contains it — all others are ignored.  When different version groups
        produce separate merged RPs, one group's player.json wins and the others'
        animation/variable definitions (needed by animation controllers in those
        other groups) are silently dropped.  This step creates one authoritative
        union of all groups' player.json data so every RP carries it, preventing
        cross-group 'can't find animation' and 'unknown variable' errors.
        """
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
        _ENTITY_CTX_QUERIES = (
            'query.is_item_name_any',
            'query.is_item_any_tag',
            'query.equipped_item_any_tag',
            'query.property(',
            'query.has_equippable(',
            'query.get_equipped_item_name(',
        )
        try:
            rp_paths = []
            unified = {}
            for entry in _os.scandir(output_root):
                if not entry.is_dir():
                    continue
                rp = _os.path.join(entry.path, 'resource_pack.mcpack')
                if not _os.path.isfile(rp):
                    continue
                rp_paths.append(rp)
                try:
                    with _zipfile.ZipFile(rp, 'r') as zf:
                        if 'entity/player.json' in zf.namelist():
                            data = _json.loads(zf.read('entity/player.json'))
                            self._merge_json_data(unified, data)
                except Exception:
                    pass

            if not unified or not rp_paths:
                return

            desc = unified.get('minecraft:client_entity', {}).get('description', {})
            if not isinstance(desc, dict):
                return

            scripts = desc.setdefault('scripts', {})

            # Move entity-context queries out of initialize into pre_animation
            try:
                init_raw   = scripts.get('initialize', [])
                init_list  = list(init_raw) if isinstance(init_raw, list) else []
                pre_list   = scripts.setdefault('pre_animation', [])
                if not isinstance(pre_list, list):
                    pre_list = []
                    scripts['pre_animation'] = pre_list
                keep_init, move_pre = [], []
                for expr in init_list:
                    if isinstance(expr, str) and any(q in expr for q in _ENTITY_CTX_QUERIES):
                        move_pre.append(expr)
                    else:
                        keep_init.append(expr)
                if move_pre:
                    scripts['initialize'] = keep_init
                    existing_pre = ' '.join(str(x) for x in pre_list)
                    for mv in move_pre:
                        if mv not in existing_pre:
                            pre_list.append(mv)
            except Exception:
                pass

            # De-duplicate: remove from pre_animation any simple variable
            # initializations (variable.X = N;) that already appear in initialize.
            # Having them in both resets the variable every frame, breaking
            # addons that dynamically change that variable (e.g. melee_spear_equipped).
            try:
                _init_for_dedup = scripts.get('initialize', [])
                _pre_for_dedup  = scripts.get('pre_animation', [])
                if isinstance(_init_for_dedup, list) and isinstance(_pre_for_dedup, list):
                    _init_text = ' '.join(str(x) for x in _init_for_dedup)
                    _clean_pre = []
                    for _pe_expr in _pre_for_dedup:
                        if not isinstance(_pe_expr, str):
                            _clean_pre.append(_pe_expr)
                            continue
                        # Simple zero-init pattern: variable.X = <literal>;
                        _is_simple_init = (
                            _pe_expr.strip().startswith('variable.') and
                            '=' in _pe_expr and
                            not any(q in _pe_expr for q in _ENTITY_CTX_QUERIES) and
                            not any(fn in _pe_expr for fn in ('query.', 'math.', 'Math.')) and
                            _pe_expr.strip() in _init_text
                        )
                        if not _is_simple_init:
                            _clean_pre.append(_pe_expr)
                    scripts['pre_animation'] = _clean_pre
            except Exception:
                pass

            # Backfill vanilla animation aliases
            try:
                anims = desc.setdefault('animations', {})
                if not isinstance(anims, dict):
                    anims = {}
                    desc['animations'] = anims
                for alias, anim_id in _VANILLA_PLAYER_ANIMS.items():
                    anims.setdefault(alias, anim_id)
            except Exception:
                pass

            # Stub any animate-block short-names that are still missing
            try:
                animate_blk = scripts.get('animate', [])
                if isinstance(animate_blk, list):
                    defined = set(anims.keys())
                    for ent in animate_blk:
                        a = ent if isinstance(ent, str) else (next(iter(ent), None) if isinstance(ent, dict) else None)
                        if a and a not in defined:
                            anims[a] = 'animation.player.move'
                            defined.add(a)
            except Exception:
                pass

            # De-duplicate scripts.animate by name: dict-with-condition beats plain string.
            # _union_merge_list uses full JSON fingerprint, so "root" (str) and
            # {"root": "!query.is_riding"} (dict) are treated as different items and
            # both survive → the root controller runs twice → legs/arms go crazy.
            try:
                _anim_blk = scripts.get('animate', [])
                if isinstance(_anim_blk, list):
                    _anim_seen = {}
                    for _ae in _anim_blk:
                        if isinstance(_ae, str):
                            if _ae not in _anim_seen:
                                _anim_seen[_ae] = _ae
                        elif isinstance(_ae, dict) and _ae:
                            _ak = next(iter(_ae))
                            _anim_seen[_ak] = _ae  # dict wins over any earlier plain string
                    scripts['animate'] = list(_anim_seen.values())
            except Exception:
                pass

            # De-duplicate render_controllers by controller name (first occurrence wins).
            # Multiple packs list the same render controller with slightly different condition
            # strings (spacing) → all survive → player renders multiple times simultaneously.
            try:
                _rc_list = desc.get('render_controllers', [])
                if isinstance(_rc_list, list):
                    _rc_seen = {}
                    for _rce in _rc_list:
                        if isinstance(_rce, dict) and _rce:
                            _rcn = next(iter(_rce))
                            if _rcn not in _rc_seen:
                                _rc_seen[_rcn] = _rce
                        elif isinstance(_rce, str) and _rce not in _rc_seen:
                            _rc_seen[_rce] = _rce
                    desc['render_controllers'] = list(_rc_seen.values())
            except Exception:
                pass

            unified_str = _json.dumps(unified, indent=2)

            # Write the unified player.json back into every group's resource_pack.mcpack
            for rp in rp_paths:
                _tmpfd, _tmppath = None, None
                try:
                    _tmpfd, _tmppath = _tempfile.mkstemp(
                        dir=_os.path.dirname(rp), suffix='.autobe_tmp')
                    _os.close(_tmpfd)
                    _tmpfd = None
                    with _zipfile.ZipFile(rp, 'r') as zin:
                        with _zipfile.ZipFile(_tmppath, 'w', _zipfile.ZIP_DEFLATED) as zout:
                            wrote_player = False
                            for item in zin.infolist():
                                if item.filename in ('entity/player.json', 'entity/player.entity.json'):
                                    if not wrote_player:
                                        zout.writestr('entity/player.entity.json', unified_str)
                                        wrote_player = True
                                    # drop duplicate entry
                                else:
                                    zout.writestr(item, zin.read(item.filename))
                            if not wrote_player:
                                zout.writestr('entity/player.entity.json', unified_str)
                    _os.replace(_tmppath, rp)
                    _tmppath = None
                except Exception:
                    pass
                finally:
                    if _tmpfd is not None:
                        try:
                            _os.close(_tmpfd)
                        except Exception:
                            pass
                    if _tmppath and _os.path.exists(_tmppath):
                        try:
                            _os.unlink(_tmppath)
                        except Exception:
                            pass
        except Exception:
            pass

    def _unify_cross_group_player_anims(self, output_root):
        """Merge player animation / animation-controller / render-controller files
        from ALL groups' RPs into unified files and write them back to every group.

        When different version groups produce separate merged RPs (e.g. 'none' for
        Play-as-Link, '1_x' for Paraglider), Bedrock can only honour ONE group's
        animations/player.animation.json — the one in the highest-priority RP.  The
        other groups' custom animations are silently lost.  This step creates one
        authoritative union of all groups' player animation data so every RP carries
        the complete set, regardless of load order.

        Merge strategy: first-wins per individual animation / controller ID.
        Each animation is a self-contained definition; partially merging two packs'
        versions of the same animation produces broken keyframes, so we keep the
        first-encountered complete definition and add any IDs not yet seen.
        """
        _PLAYER_ANIM_FILES = [
            'animations/player.animation.json',
            'animations/player_firstperson.animation.json',
            'animation_controllers/player.animation_controllers.json',
            'render_controllers/player.render_controllers.json',
            'entity/player.entity.json',
        ]
        # Top-level dict keys that hold individual named entries (first-wins per entry)
        _ENTRY_DICT_KEYS = {'animations', 'animation_controllers', 'render_controllers', 'minecraft:client_entity'}

        def _merge_anim_first_wins(target, source):
            """Merge source into target with first-wins per named animation/controller entry."""
            for k, v in source.items():
                if k not in target:
                    target[k] = v
                elif k in _ENTRY_DICT_KEYS and isinstance(target[k], dict) and isinstance(v, dict):
                    for entry_id, entry_data in v.items():
                        target[k].setdefault(entry_id, entry_data)
                # Special handling for description section in entity files
                elif k == 'description' and isinstance(target[k], dict) and isinstance(v, dict):
                    # Prioritize source description entirely to preserve custom features
                    target[k] = v
                # primitives like format_version: keep first (do nothing)

        def _merge_mobs_json(target, source):
            """Merge models/mobs.json: union geometry IDs + bone-union per geometry.
            mobs.json top-level keys are geometry IDs (e.g. 'geometry.humanoid.custom:...')
            that each contain a 'bones' list.  Different packs ship slightly different
            versions — e.g. BetterCombat is missing the 'hat' bone that the Link Pack
            adds to geometry.humanoid.custom.  This union ensures every bone that any
            pack defines is present in the final merged geometry.
            """
            for k, v in source.items():
                if k == 'format_version':
                    target.setdefault(k, v)
                elif k not in target:
                    # New geometry ID: add it entirely
                    target[k] = v
                elif isinstance(target[k], dict) and isinstance(v, dict):
                    # Same geometry ID in two packs: union bones by name
                    if isinstance(target[k].get('bones'), list) and isinstance(v.get('bones'), list):
                        _existing_names = {b.get('name') for b in target[k]['bones'] if isinstance(b, dict)}
                        for _bone in v['bones']:
                            if isinstance(_bone, dict) and _bone.get('name') not in _existing_names:
                                target[k]['bones'].append(_bone)
                                _existing_names.add(_bone.get('name'))

        try:
            rp_paths = []
            unified = {p: None for p in _PLAYER_ANIM_FILES}
            unified_mobs = None   # models/mobs.json: bone-union merge
            player_textures = {}  # path → bytes, player texture files that only exist in one group

            for entry in sorted(_os.scandir(output_root), key=lambda e: e.name, reverse=True):
                if not entry.is_dir():
                    continue
                rp = _os.path.join(entry.path, 'resource_pack.mcpack')
                if not _os.path.isfile(rp):
                    continue
                rp_paths.append(rp)
                _logging.info(f"[_unify_cross_group_player_anims] Processing RP: {rp}")
                try:
                    with _zipfile.ZipFile(rp, 'r') as zf:
                        names = zf.namelist()
                        for anim_file in _PLAYER_ANIM_FILES:
                            if anim_file in names:
                                try:
                                    data = _json.loads(zf.read(anim_file))
                                    if unified[anim_file] is None:
                                        import copy as _copy
                                        unified[anim_file] = _copy.deepcopy(data)
                                        _logging.info(f"[_unify_cross_group_player_anims] Initialized {anim_file} from {rp}")
                                    else:
                                        _merge_anim_first_wins(unified[anim_file], data)
                                        _logging.info(f"[_unify_cross_group_player_anims] Merged {anim_file} from {rp}")
                                except Exception as _e:
                                    _logging.error(f"[_unify_cross_group_player_anims] Failed to process {anim_file} in {rp}: {_e}", exc_info=True)
                        # Bone-union merge for models/mobs.json
                        if 'models/mobs.json' in names:
                            try:
                                import copy as _copy
                                mobs_data = _json.loads(zf.read('models/mobs.json'))
                                if unified_mobs is None:
                                    unified_mobs = _copy.deepcopy(mobs_data)
                                    _logging.info(f"[_unify_cross_group_player_anims] Initialized models/mobs.json from {rp}")
                                else:
                                    _merge_mobs_json(unified_mobs, mobs_data)
                                    _logging.info(f"[_unify_cross_group_player_anims] Merged models/mobs.json from {rp}")
                            except Exception as _e:
                                _logging.error(f"[_unify_cross_group_player_anims] Failed to process models/mobs.json in {rp}: {_e}", exc_info=True)
                        # Collect player-specific textures that only exist in this RP
                        # (e.g. Link Pack's textures/entity/steve.png)
                        for _tex_name in names:
                            if not _tex_name.startswith('textures/entity/') or not _tex_name.endswith('.png'):
                                continue
                            # Only collect if not already seen in another group
                            if _tex_name not in player_textures:
                                try:
                                    player_textures[_tex_name] = zf.read(_tex_name)
                                except Exception as _e:
                                    _logging.error(f"[_unify_cross_group_player_anims] Failed to read texture {_tex_name} in {rp}: {_e}", exc_info=True)
                except Exception as _e:
                    _logging.error(f"[_unify_cross_group_player_anims] Failed to process RP {rp}: {_e}", exc_info=True)

            if not rp_paths:
                _logging.warning("[_unify_cross_group_player_anims] No resource packs found to process")
                return

            serialised = {}
            for anim_file, data in unified.items():
                if data:
                    serialised[anim_file] = _json.dumps(data, indent=2)
            if unified_mobs:
                serialised['models/mobs.json'] = _json.dumps(unified_mobs, indent=2)

            if not serialised and not player_textures:
                _logging.warning("[_unify_cross_group_player_anims] No data to write back")
                return

            _logging.info(f"[_unify_cross_group_player_anims] Writing unified files to {len(rp_paths)} RPs: {list(serialised.keys())}")

            for rp in rp_paths:
                _tmpfd, _tmppath = None, None
                try:
                    _tmpfd, _tmppath = _tempfile.mkstemp(
                        dir=_os.path.dirname(rp), suffix='.autobe_tmp')
                    _os.close(_tmpfd)
                    _tmpfd = None
                    with _zipfile.ZipFile(rp, 'r') as zin:
                        with _zipfile.ZipFile(_tmppath, 'w', _zipfile.ZIP_DEFLATED) as zout:
                            written = set()
                            for item in zin.infolist():
                                if item.filename in serialised:
                                    zout.writestr(item, serialised[item.filename])
                                    written.add(item.filename)
                                else:
                                    zout.writestr(item, zin.read(item.filename))
                            for anim_file, content in serialised.items():
                                if anim_file not in written:
                                    zout.writestr(anim_file, content)
                                    written.add(anim_file)
                            # Distribute player-specific textures to all groups
                            for _tex_path, _tex_data in player_textures.items():
                                if _tex_path not in written and _tex_path not in [n.filename for n in zin.infolist()]:
                                    zout.writestr(_tex_path, _tex_data)
                    _os.replace(_tmppath, rp)
                    _tmppath = None
                    _logging.info(f"[_unify_cross_group_player_anims] Successfully updated {rp}")
                except Exception as _e:
                    _logging.error(f"[_unify_cross_group_player_anims] Failed to update RP {rp}: {_e}", exc_info=True)
                finally:
                    if _tmpfd is not None:
                        try:
                            _os.close(_tmpfd)
                        except Exception:
                            pass
                    if _tmppath and _os.path.exists(_tmppath):
                        try:
                            _os.unlink(_tmppath)
                        except Exception:
                            pass
        except Exception as _e:
            _logging.error(f"[_unify_cross_group_player_anims] Top-level exception: {_e}", exc_info=True)

    def _unify_cross_group_atlas_files(self, output_root):
        """Merge terrain_texture.json, item_texture.json, and blocks.json from ALL
        groups' merged RPs into one unified set and write it back to every group.

        Custom blocks whose BP lives in one version group (e.g. 2_x) keep their
        terrain_texture / item_texture registrations inside that group's RP only.
        When Bedrock applies multiple merged RPs, it may not reliably merge
        terrain_texture.json from a lower-priority pack (behaviour varies across
        engine versions and RP-stack orderings).  A block defined in the 2_x BP
        referencing texture ID 'warped_planks' would therefore not find its
        registration in the 1_x RP (which has no entry for it) and fall back to
        the missing-texture dirt appearance.

        Fix: union all groups' texture_data (first-wins per entry so no pack can
        silently overwrite another's custom texture IDs) and write the combined
        atlas to every group's resource_pack.mcpack.
        """
        _ATLAS_FILES = [
            'textures/terrain_texture.json',
            'textures/item_texture.json',
            'blocks.json',
        ]
        try:
            rp_paths = []
            unified = {f: None for f in _ATLAS_FILES}

            for entry in sorted(_os.scandir(output_root), key=lambda e: e.name):
                if not entry.is_dir():
                    continue
                rp = _os.path.join(entry.path, 'resource_pack.mcpack')
                if not _os.path.isfile(rp):
                    continue
                rp_paths.append(rp)
                try:
                    with _zipfile.ZipFile(rp, 'r') as zf:
                        names = zf.namelist()
                        for atlas_file in _ATLAS_FILES:
                            if atlas_file not in names:
                                continue
                            try:
                                import copy as _copy
                                data = _json.loads(zf.read(atlas_file))
                                if unified[atlas_file] is None:
                                    unified[atlas_file] = _copy.deepcopy(data)
                                else:
                                    # Union merge: recurse into 'texture_data' or top-level
                                    # dict, keeping first-wins for conflicting IDs so each
                                    # pack's own texture registrations are always preserved.
                                    _base = unified[atlas_file]
                                    for k, v in data.items():
                                        if k not in _base:
                                            _base[k] = v
                                        elif isinstance(_base[k], dict) and isinstance(v, dict):
                                            # texture_data / item entries: first-wins per key
                                            for ek, ev in v.items():
                                                _base[k].setdefault(ek, ev)
                                        # primitives (format_version, etc.): keep first
                            except Exception:
                                pass
                except Exception:
                    pass

            if not rp_paths:
                return

            serialised = {}
            for atlas_file, data in unified.items():
                if data:
                    serialised[atlas_file] = _json.dumps(data, indent=2)

            if not serialised:
                return

            # --- Geometry distribution ---
            # Collect models/entity/*.geo.json and models/blocks/*.geo.json from all
            # groups.  For each unique path union-merge the minecraft:geometry arrays
            # (first-wins per geometry ID) so every group ends up with the full set.
            # This ensures geometry.table / geometry.chair (only in 2_x RP) are found
            # when 1_x RP is the highest-priority active pack.
            _geo_prefixes = ('models/entity/', 'models/blocks/')
            _geo_unified = {}   # path -> merged geometry JSON data
            for _rp2 in rp_paths:
                try:
                    with _zipfile.ZipFile(_rp2, 'r') as _zf2:
                        for _n in _zf2.namelist():
                            if not any(_n.startswith(_p) for _p in _geo_prefixes):
                                continue
                            if not _n.endswith('.geo.json'):
                                continue
                            try:
                                import copy as _copy
                                _gdata = _json.loads(_zf2.read(_n))
                                if _n not in _geo_unified:
                                    _geo_unified[_n] = _copy.deepcopy(_gdata)
                                else:
                                    # Union-merge minecraft:geometry arrays
                                    _base_g = _geo_unified[_n]
                                    _src_g = _gdata
                                    if (isinstance(_base_g.get('minecraft:geometry'), list)
                                            and isinstance(_src_g.get('minecraft:geometry'), list)):
                                        _existing_ids = {
                                            g.get('description', {}).get('identifier')
                                            for g in _base_g['minecraft:geometry']
                                            if isinstance(g, dict)
                                        }
                                        for _geo_entry in _src_g['minecraft:geometry']:
                                            _eid = (_geo_entry.get('description', {}).get('identifier')
                                                    if isinstance(_geo_entry, dict) else None)
                                            if _eid not in _existing_ids:
                                                _base_g['minecraft:geometry'].append(_geo_entry)
                                                _existing_ids.add(_eid)
                            except Exception:
                                pass
                except Exception:
                    pass

            # Serialise merged geometry files
            _geo_serialised = {}
            for _geo_path, _geo_data in _geo_unified.items():
                try:
                    _geo_serialised[_geo_path] = _json.dumps(_geo_data, indent=2)
                except Exception:
                    pass

            for rp in rp_paths:
                _tmpfd, _tmppath = None, None
                try:
                    _tmpfd, _tmppath = _tempfile.mkstemp(
                        dir=_os.path.dirname(rp), suffix='.autobe_tmp')
                    _os.close(_tmpfd)
                    _tmpfd = None
                    with _zipfile.ZipFile(rp, 'r') as zin:
                        with _zipfile.ZipFile(_tmppath, 'w', _zipfile.ZIP_DEFLATED) as zout:
                            written = set()
                            for item in zin.infolist():
                                if item.filename in serialised:
                                    zout.writestr(item, serialised[item.filename])
                                    written.add(item.filename)
                                elif item.filename in _geo_serialised:
                                    zout.writestr(item, _geo_serialised[item.filename])
                                    written.add(item.filename)
                                else:
                                    zout.writestr(item, zin.read(item.filename))
                            for atlas_file, content in serialised.items():
                                if atlas_file not in written:
                                    zout.writestr(atlas_file, content)
                            for _geo_path, _geo_content in _geo_serialised.items():
                                if _geo_path not in written:
                                    zout.writestr(_geo_path, _geo_content)
                    _os.replace(_tmppath, rp)
                    _tmppath = None
                except Exception:
                    pass
                finally:
                    if _tmpfd is not None:
                        try:
                            _os.close(_tmpfd)
                        except Exception:
                            pass
                    if _tmppath and _os.path.exists(_tmppath):
                        try:
                            _os.unlink(_tmppath)
                        except Exception:
                            pass
        except Exception:
            pass

    def _unify_cross_group_hud_files(self, output_root):
        """Merge ui/hud_screen.json and ui/_ui_defs.json from ALL groups' RPs into
        one unified file and write it back to every group's resource_pack.mcpack.

        When different version groups produce separate merged RPs, Bedrock only
        honours one pack's hud_screen.json modifications per key — the others are
        silently lost.  For example, Paraglider's 150 KB hud_screen (1_x RP) would
        override the temperature/mqps HUD patches (2_x RP), causing temperature
        state text to show as raw title text and mqps bars to render incorrectly.
        This step creates one authoritative union of all groups' UI modifications so
        every RP carries the complete hud_screen and _ui_defs registration list.
        """
        try:
            _UI_FILES = ['ui/hud_screen.json', 'ui/_global_variables.json']
            _UI_DEFS  = 'ui/_ui_defs.json'

            rp_paths = []
            # merged_hud[file_path] = combined dict
            merged = {p: {} for p in _UI_FILES}
            merged_ui_defs = []          # deduplicated list of ui_def entries
            merged_ui_defs_set = set()
            # .uids patches: path → (old, new) string replacements
            # NOTE: hud_temp.uids correctly uses source_control_name:"temp_data_binding"
            # which matches the element injected into root_panel as
            # "temp_data_binding@hud_wt_temp.temp_data" by the Water Temperature
            # System's hud_screen.json.  No patch is needed here.
            _UIDS_PATCHES = {}
            # Collect .uids files that need patching across all RPs
            uids_to_patch = {}   # path → raw content after patching

            for entry in sorted(_os.scandir(output_root), key=lambda e: e.name):
                if not entry.is_dir():
                    continue
                rp = _os.path.join(entry.path, 'resource_pack.mcpack')
                if not _os.path.isfile(rp):
                    continue
                rp_paths.append(rp)
                try:
                    with _zipfile.ZipFile(rp, 'r') as zf:
                        names = zf.namelist()
                        # Merge plain UI JSON files (dict union, later groups win)
                        for ui_path in _UI_FILES:
                            if ui_path in names:
                                try:
                                    raw = zf.read(ui_path).decode('utf-8', 'replace')
                                    data = _json.loads(_re.sub(r'//[^\n]*', '', raw))
                                    # Special handling for factories: first-wins to preserve MQPS functionality
                                    if ui_path == 'ui/hud_screen.json':
                                        # Preserve factories with first-wins strategy
                                        for key, value in data.items():
                                            if 'factory' in key.lower():
                                                if key not in merged[ui_path]:
                                                    merged[ui_path][key] = value
                                            elif key == 'hud_actionbar_text' and '$atext' in value:
                                                # Preserve $atext binding from MQPS
                                                if key not in merged[ui_path] or '$atext' not in merged[ui_path][key]:
                                                    merged[ui_path][key] = value
                                            else:
                                                # Normal merge for other elements
                                                self._deep_merge_dicts(merged[ui_path], {key: value},
                                                                       _combine_visible=True)
                                    else:
                                        # Normal merge for other UI files
                                        self._deep_merge_dicts(merged[ui_path], data,
                                                               _combine_visible=True)
                                except Exception:
                                    pass
                        # Merge _ui_defs.json arrays (union, preserve order)
                        if _UI_DEFS in names:
                            try:
                                raw = zf.read(_UI_DEFS).decode('utf-8', 'replace')
                                defs_data = _json.loads(_re.sub(r'//[^\n]*', '', raw))
                                for entry_def in defs_data.get('ui_defs', []):
                                    if entry_def not in merged_ui_defs_set:
                                        merged_ui_defs.append(entry_def)
                                        merged_ui_defs_set.add(entry_def)
                            except Exception:
                                pass
                        # Collect and patch known-broken .uids files
                        for uids_path, patches in _UIDS_PATCHES.items():
                            if uids_path in names:
                                try:
                                    raw = zf.read(uids_path).decode('utf-8', 'replace')
                                    for old, new in patches:
                                        raw = raw.replace(old, new)
                                    uids_to_patch[uids_path] = raw.encode('utf-8')
                                except Exception:
                                    pass
                        # Collect ALL .uids files for cross-group distribution.
                        # Each group's _ui_defs.json now lists entries from all
                        # groups, so every group's RP must physically contain the
                        # referenced .uids files — even if the originating pack
                        # was only in one group.  Last-writer-wins across groups
                        # is fine since the files are identical across groups.
                        for _uids_name in names:
                            if _uids_name.endswith('.uids') and _uids_name not in uids_to_patch:
                                try:
                                    uids_to_patch[_uids_name] = zf.read(_uids_name)
                                except Exception:
                                    pass
                except Exception:
                    pass

            if not rp_paths:
                return

            # NOTE: Do NOT replace $atext with #actionbar_text here.
            # MQPS uses hud_actionbar_text_factory which provides $actionbar_text as a
            # factory-scoped variable to all factory-instantiated elements (hud_actionbar
            # _text, more_hunger_bar, more_health_bar).  $atext='$actionbar_text' resolves
            # correctly inside this factory context.  Using #actionbar_text in a Molang
            # 'visible' expression does NOT work — # bindings are text-property-only and
            # evaluate to 0 in Molang arithmetic → '%.4s'*0='' ≠ 'mqps' → NOT false=TRUE
            # → hud_actionbar_text ALWAYS visible → raw 'mqps...' text always bleeds.

            # Serialise merged results
            serialised = {}        # path → str  (for JSON files)
            serialised_bin = {}    # path → bytes (for binary/uids files)
            for ui_path, data in merged.items():
                if data:
                    serialised[ui_path] = _json.dumps(data, indent=2, ensure_ascii=False)
            if merged_ui_defs:
                serialised[_UI_DEFS] = _json.dumps({'ui_defs': merged_ui_defs}, indent=2, ensure_ascii=False)
            for uids_path, content_bytes in uids_to_patch.items():
                serialised_bin[uids_path] = content_bytes

            if not serialised and not serialised_bin:
                return

            # Write unified files back into every group's resource_pack.mcpack
            for rp in rp_paths:
                _tmpfd, _tmppath = None, None
                try:
                    _tmpfd, _tmppath = _tempfile.mkstemp(
                        dir=_os.path.dirname(rp), suffix='.autobe_tmp')
                    _os.close(_tmpfd)
                    _tmpfd = None
                    with _zipfile.ZipFile(rp, 'r') as zin:
                        with _zipfile.ZipFile(_tmppath, 'w', _zipfile.ZIP_DEFLATED) as zout:
                            written = set()
                            for item in zin.infolist():
                                if item.filename in serialised:
                                    zout.writestr(item, serialised[item.filename])
                                    written.add(item.filename)
                                elif item.filename in serialised_bin:
                                    zout.writestr(item, serialised_bin[item.filename])
                                    written.add(item.filename)
                                else:
                                    zout.writestr(item, zin.read(item.filename))
                            # Add any files that existed in other groups but not this one
                            for ui_path, content in serialised.items():
                                if ui_path not in written:
                                    zout.writestr(ui_path, content)
                            for ui_path, content in serialised_bin.items():
                                if ui_path not in written:
                                    zout.writestr(ui_path, content)
                    _os.replace(_tmppath, rp)
                    _tmppath = None
                except Exception:
                    pass
                finally:
                    if _tmpfd is not None:
                        try:
                            _os.close(_tmpfd)
                        except Exception:
                            pass
                    if _tmppath and _os.path.exists(_tmppath):
                        try:
                            _os.unlink(_tmppath)
                        except Exception:
                            pass
        except Exception:
            pass

    def _merge_subpack_hud_files(self, output_root):
        """For every subpack inside a merged RP that contains ui/hud_screen.json,
        merge the merged root hud_screen.json into that subpack file so selecting
        a subpack variant (e.g. SWAILA position) does not discard the merged root
        HUD patches (mqps bars, temperature overlay, Paraglider UI, …).

        Strategy: merged-root is the base; subpack changes are applied on top
        (last-wins for primitives so the subpack's positioning/visibility wins,
        first-seen entries for new keys).
        """
        try:
            for entry in _os.scandir(output_root):
                if not entry.is_dir():
                    continue
                rp = _os.path.join(entry.path, 'resource_pack.mcpack')
                if not _os.path.isfile(rp):
                    continue
                try:
                    with _zipfile.ZipFile(rp, 'r') as zf:
                        names = zf.namelist()
                        # Find root hud_screen
                        if 'ui/hud_screen.json' not in names:
                            continue
                        try:
                            root_hud = _json.loads(zf.read('ui/hud_screen.json'))
                        except Exception:
                            continue
                        # Find subpack hud_screen.json files
                        sub_hud_paths = [
                            n for n in names
                            if n.startswith('subpacks/') and n.endswith('/ui/hud_screen.json')
                        ]
                        if not sub_hud_paths:
                            continue
                        # Build merged subpack versions
                        merged_subs = {}
                        for sub_path in sub_hud_paths:
                            try:
                                sub_data = _json.loads(zf.read(sub_path))
                                import copy as _copy
                                combined = _copy.deepcopy(root_hud)
                                self._deep_merge_dicts(combined, sub_data,
                                                       _combine_visible=True)
                                merged_subs[sub_path] = _json.dumps(combined, indent=2,
                                                                     ensure_ascii=False)
                            except Exception:
                                pass
                        if not merged_subs:
                            continue
                    # Rewrite RP with updated subpack hud_screen files
                    _tmpfd, _tmppath = None, None
                    try:
                        _tmpfd, _tmppath = _tempfile.mkstemp(
                            dir=_os.path.dirname(rp), suffix='.autobe_tmp')
                        _os.close(_tmpfd)
                        _tmpfd = None
                        with _zipfile.ZipFile(rp, 'r') as zin:
                            with _zipfile.ZipFile(_tmppath, 'w',
                                                  _zipfile.ZIP_DEFLATED) as zout:
                                for item in zin.infolist():
                                    if item.filename in merged_subs:
                                        zout.writestr(item,
                                                      merged_subs[item.filename])
                                    else:
                                        zout.writestr(item,
                                                      zin.read(item.filename))
                        _os.replace(_tmppath, rp)
                        _tmppath = None
                    except Exception:
                        pass
                    finally:
                        if _tmpfd is not None:
                            try:
                                _os.close(_tmpfd)
                            except Exception:
                                pass
                        if _tmppath and _os.path.exists(_tmppath):
                            try:
                                _os.unlink(_tmppath)
                            except Exception:
                                pass
                except Exception:
                    pass
        except Exception:
            pass

    def _deep_merge_dicts(self, base, overlay, _combine_visible=False):
        """Recursively merge overlay into base in-place.
        Lists are replaced (not appended) to avoid duplicating UI element arrays.
        Exception: 'modifications' lists are concatenated so every pack's UI
        injection operations (insert_front/insert_after/etc.) are all preserved.
        When _combine_visible is True, 'visible' string values are combined with
        ' && ' instead of replaced, preserving each pack's UI visibility conditions.
        """
        for k, v in overlay.items():
            if k in base and isinstance(base[k], dict) and isinstance(v, dict):
                self._deep_merge_dicts(base[k], v, _combine_visible=_combine_visible)
            elif (_combine_visible and k == 'visible'
                  and isinstance(base.get(k), str) and isinstance(v, str)
                  and base[k] != v):
                base[k] = f'({base[k]}) && ({v})'
            elif (k == 'modifications'
                  and isinstance(base.get(k), list) and isinstance(v, list)):
                base[k] = base[k] + v
            else:
                base[k] = v

    def _extract_entity_identifier_from_json(self, data):
        """Return the identifier string from already-loaded entity JSON, or None."""
        for key in ('minecraft:entity', 'minecraft:client_entity'):
            if key in data:
                identifier = data[key].get('description', {}).get('identifier')
                if identifier and identifier != 'minecraft:player':
                    return identifier
        return None

    def _extract_item_identifier_from_json(self, data):
        """Return the identifier string from already-loaded item JSON, or None."""
        if 'minecraft:item' in data:
            return data['minecraft:item'].get('description', {}).get('identifier')
        return None

    def _extract_block_identifier_from_json(self, data):
        """Return the identifier string from already-loaded block JSON, or None."""
        if 'minecraft:block' in data:
            return data['minecraft:block'].get('description', {}).get('identifier')
        return None
