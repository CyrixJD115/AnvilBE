class AutoBEApp:



    def _send_discord_merge_log(self, pack_files):
        """Send merge log to Discord webhook with addon names, creators, and actual pack icons."""
        webhook_url = "https://discord.com/api/webhooks/1510724383042441397/Bi0UFejBJeohSNCv_nw0JaDPEjXdG1ljDUgDOVFltJ5ZSHL2NbfA4jk_Yaf1A21hJa3K"
        
        if not pack_files:
            return
        
        _logging.info(f"Discord merge log: Processing {len(pack_files)} pack files")
        
        # Deduplicate addons by manifest name (most reliable method)
        seen_manifest_names = set()
        seen_file_paths = set()
        unique_addons = []
        
        for pack_file in pack_files:
            try:
                # Extract addon name from manifest.json
                addon_name = None
                with _zipfile.ZipFile(pack_file, 'r') as zf:
                    if 'manifest.json' in zf.namelist():
                        try:
                            manifest_bytes = zf.read('manifest.json')
                            # Handle manifests with extra data/comments after JSON
                            manifest_str = manifest_bytes.decode('utf-8')
                            # Find the closing brace of the JSON object
                            brace_count = 0
                            json_end = -1
                            for i, char in enumerate(manifest_str):
                                if char == '{':
                                    brace_count += 1
                                elif char == '}':
                                    brace_count -= 1
                                    if brace_count == 0:
                                        json_end = i + 1
                                        break
                            if json_end > 0:
                                manifest_str = manifest_str[:json_end]
                            manifest_data = _json.loads(manifest_str)
                            addon_name = manifest_data.get('header', {}).get('name')
                        except:
                            pass
                
                # If manifest name is available, use it for deduplication
                if addon_name:
                    # Strip BP/RP suffixes and _1, _2, etc. from manifest name for deduplication
                    base_name = _re.sub(
                        r'[_\-\s]*(bp|rp|behaviors?|resources?|behavior[_\-]?pack|resource[_\-]?pack|[_\-\s]*\d+)$',
                        '', addon_name, flags=_re.IGNORECASE).lower()
                    _logging.info(f"Pack: {pack_file}, Manifest name: {addon_name}, Base name: {base_name}")
                    
                    if base_name in seen_manifest_names:
                        _logging.info(f"Filtered as duplicate (manifest): {base_name}")
                        continue
                    seen_manifest_names.add(base_name)
                    unique_addons.append(pack_file)
                    _logging.info(f"Added to unique addons (manifest): {base_name}")
                else:
                    # No manifest name - use filename for deduplication
                    filename = _os.path.basename(pack_file)
                    # Strip _1, _2, RP, BP suffixes from filename
                    base_filename = _re.sub(
                        r'[_\-\s]*(bp|rp|behaviors?|resources?|behavior[_\-]?pack|resource[_\-]?pack|[_\-\s]*\d+)$',
                        '', filename, flags=_re.IGNORECASE).lower()
                    _logging.info(f"Pack: {pack_file}, No manifest name, using filename: {base_filename}")
                    
                    if base_filename in seen_file_paths:
                        _logging.info(f"Filtered as duplicate (filename): {base_filename}")
                        continue
                    seen_file_paths.add(base_filename)
                    unique_addons.append(pack_file)
                    _logging.info(f"Added to unique addons (filename): {base_filename}")
            except Exception as e:
                _logging.warning(f"Failed to deduplicate {pack_file}: {e}")
                unique_addons.append(pack_file)
        
        _logging.info(f"Discord merge log: After deduplication, {len(unique_addons)} unique addons out of {len(pack_files)} total files")
        
        addon_info = []
        for pack_file in unique_addons:
            try:
                with _zipfile.ZipFile(pack_file, 'r') as zf:
                    # Extract addon name and creator from manifest.json
                    addon_name = _os.path.basename(pack_file)
                    creator = "Unknown"
                    pack_icon_data = None
                    
                    if 'manifest.json' in zf.namelist():
                        try:
                            manifest_bytes = zf.read('manifest.json')
                            # Handle manifests with extra data/comments after JSON
                            manifest_str = manifest_bytes.decode('utf-8')
                            # Find the closing brace of the JSON object
                            brace_count = 0
                            json_end = -1
                            for i, char in enumerate(manifest_str):
                                if char == '{':
                                    brace_count += 1
                                elif char == '}':
                                    brace_count -= 1
                                    if brace_count == 0:
                                        json_end = i + 1
                                        break
                            if json_end > 0:
                                manifest_str = manifest_str[:json_end]
                            manifest_data = _json.loads(manifest_str)
                            manifest_name = manifest_data.get('header', {}).get('name', addon_name)
                            # Use filename if manifest name is a placeholder
                            if manifest_name and manifest_name.lower() in ('pack.name', 'pack.description', ''):
                                addon_name = _os.path.basename(pack_file)
                            else:
                                addon_name = manifest_name
                            # Try to extract creator from description or authors field
                            description = manifest_data.get('header', {}).get('description', '')
                            # Check both header.authors and metadata.authors
                            header_authors = manifest_data.get('header', {}).get('authors', [])
                            metadata_authors = manifest_data.get('metadata', {}).get('authors', [])
                            authors = header_authors or metadata_authors
                            
                            _logging.info(f"Pack: {addon_name}, header_authors: {header_authors}, metadata_authors: {metadata_authors}, final_authors: {authors}")
                            
                            if authors:
                                if isinstance(authors, list):
                                    creator = ', '.join(authors)
                                else:
                                    creator = str(authors)
                            elif description:
                                # Check for placeholder descriptions
                                if description.lower() in ('pack.description', 'pack.name', ''):
                                    creator = 'Unknown'
                                else:
                                    # Try to find creator in description
                                    import re as _re
                                    # Look for "by" pattern
                                    match = _re.search(r'by\s+([^\n]+)', description, _re.IGNORECASE)
                                    if match:
                                        creator = match.group(1).strip()
                                    else:
                                        # Try to extract from end of description (last comma-separated value)
                                        parts = [p.strip() for p in description.replace(',', '\n').split('\n')]
                                        if parts:
                                            last_part = parts[-1]
                                            # If last part is short (likely a name), use it
                                            if len(last_part) < 50 and not any(c in last_part for c in '.!?'):
                                                creator = last_part
                                            else:
                                                # Description is too long, probably not a creator name
                                                creator = 'Unknown'
                                        else:
                                            creator = 'Unknown'
                        except Exception as e:
                            _logging.warning(f"Failed to parse manifest for {pack_file}: {e}")
                    
                    # Extract pack_icon.png if present
                    if 'pack_icon.png' in zf.namelist():
                        try:
                            pack_icon_data = zf.read('pack_icon.png')
                        except Exception as e:
                            _logging.warning(f"Failed to extract pack_icon from {pack_file}: {e}")
                    
                    addon_info.append({
                        'name': addon_name,
                        'creator': creator,
                        'description': description,
                        'icon_data': pack_icon_data
                    })
            except Exception as e:
                _logging.warning(f"Failed to extract info from {pack_file}: {e}")
        
        # Create multiple embeds - one per addon, each with its own thumbnail
        # Split into batches to avoid Discord payload size limits (10 embeds per batch)
        batch_size = 10
        total_batches = (len(addon_info) + batch_size - 1) // batch_size
        
        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, len(addon_info))
            batch_addons = addon_info[start_idx:end_idx]
            
            embeds = []
            files = {}
            for i, addon in enumerate(batch_addons, start=start_idx):
                # Clean up description
                desc = addon.get('description', '')
                # Remove placeholder descriptions
                if desc.lower() in ('pack.description', 'pack.name', ''):
                    desc = 'No description'
                else:
                    # Remove creator name from end of description if present
                    creator = addon.get('creator', '')
                    if creator and creator != 'Unknown':
                        # Try to remove creator from end of description
                        if desc.endswith(creator):
                            desc = desc[:-len(creator)].strip()
                            # Remove trailing comma/whitespace
                            desc = desc.rstrip(', ').strip()
                        # Also try removing with comma
                        if desc.endswith(', ' + creator):
                            desc = desc[:-len(', ' + creator)].strip()
                    # If description is now empty after removing creator, use default
                    if not desc or len(desc) < 10:
                        desc = 'No description'
                
                embed = {
                    "title": f"{i + 1}. {addon['name']}",
                    "description": f"Creator: {addon['creator']}\nDescription: {desc}",
                    "color": 3447003,
                    "footer": {"text": f"AutoBE by CodeNex • Batch {batch_num + 1}/{total_batches}"},
                    "timestamp": _datetime.datetime.now().isoformat()
                }
                
                # Use addon's icon as thumbnail if available
                if addon['icon_data']:
                    embed["thumbnail"] = {"url": f"attachment://icon_{i}.png"}
                    files[f"icon_{i}.png"] = addon['icon_data']
                
                embeds.append(embed)
            
            # Send batch to Discord webhook
            try:
                payload = {
                    "embeds": embeds
                }
                
                if files:
                    response = _requests.post(webhook_url, data={"payload_json": _json.dumps(payload)}, files=files, timeout=30)
                else:
                    response = _requests.post(webhook_url, json=payload, timeout=10)
                
                response.raise_for_status()
                _logging.info(f"Discord merge log batch {batch_num + 1}/{total_batches} sent successfully ({len(batch_addons)} addons)")
            except Exception as e:
                _logging.warning(f"Failed to send Discord merge log batch {batch_num + 1}/{total_batches}: {e}")
        
        _logging.info(f"Discord merge log complete: {total_batches} batches, {len(addon_info)} total addons")

        # Send line breaker image at the end to separate users' merge logs
        try:
            separator_image_path = _os.path.join(_os.path.dirname(__file__), "locales", "mf.png")
            if _os.path.isfile(separator_image_path):
                with open(separator_image_path, "rb") as f:
                    separator_data = f.read()

                separator_payload = {
                    "embeds": [{
                        "image": {"url": "attachment://mf.png"},
                        "color": 3447003
                    }]
                }
                files = {"mf.png": separator_data}
                response = _requests.post(webhook_url, data={"payload_json": _json.dumps(separator_payload)}, files=files, timeout=30)
                response.raise_for_status()
                _logging.info("Discord merge log separator image sent successfully")
        except Exception as e:
            _logging.warning(f"Failed to send Discord merge log separator image: {e}")

    def _check_compatibility(self):
        _incompatible_files = []
        _missing_manifest_files = []

        _selected_files = self._files

        for _file in _selected_files:
            with _zipfile.ZipFile(_file, 'r') as _pack_zip:
                _pack_namelist = _pack_zip.namelist()

                if 'manifest.json' not in _pack_namelist:
                    _missing_manifest_files.append(_file)

        if _incompatible_files or _missing_manifest_files:
            _message = "The Following Issues Were Found With Selected MCPacks:\n\n"

            if _missing_manifest_files:
                _message += "Missing manifest.json:\n"
                for _file in _missing_manifest_files:
                    _message += f"- {_os.path.basename(_file)}\n"
                _message += "\n"

            _messagebox.showwarning("Compatibility Check", _message)
        else:
            _messagebox.showinfo(_("compatibility.title"), _("compatibility.all_have_manifest"))

    def _validate_files(self):
        invalid_files = []

        for _file in self._files:
            try:
                with _zipfile.ZipFile(_file, 'r') as _pack_zip:
                    if 'manifest.json' not in _pack_zip.namelist():
                        invalid_files.append(_file)
            except _zipfile.BadZipFile:
                invalid_files.append(_file)

        if invalid_files:
            _message = "The following files are invalid or missing manifest.json:\n\n"
            for _file in invalid_files:
                _message += f"- {_os.path.basename(_file)}\n"
            _messagebox.showerror(_("msg.invalid_files"), _message)
            _logging.error(f"Invalid files detected: {invalid_files}")
            return False
        
        return True

    def _extract_and_store_highest_versions(self):
        if not hasattr(self, 'mcpack_names'):
            _messagebox.showinfo(_("msg.error"), _("msg.no_mcpack_added"))
            return

        # Sections for storing classified packs
        sections = {
            "These Addons Are Using 1.21+ Codes": [],
            "These Addons Are Using 1.20+ Codes": [],
            "These Addons Are Using 1.19+ Codes": [],
            "These Addons Are Using 1.18+ Codes": [],
            "These Addons Are Using 1.17+ Codes": [],
            "These Addons Are Using '1.16 And Below' Codes": []
        }

        # Set initial version as low as possible for comparison
        highest_rp_version = None
        highest_bp_version = None
        
        # Set initial highest versions for dependencies, None to indicate no version found yet
        highest_server_version = None
        highest_server_ui_version = None
        highest_gametest_version = None

        # Store the actual versions (including '-beta') for manifest creation
        highest_server_version_full = None
        highest_server_ui_version_full = None
        highest_gametest_version_full = None

        for _file in self._files:
            manifest_data = self._get_manifest_data(_file)
            if manifest_data and 'header' in manifest_data and 'min_engine_version' in manifest_data['header']:
                min_engine_version_raw = manifest_data['header']['min_engine_version']
                mcpack_name = _os.path.basename(_file)

                # Normalize version to list format [major, minor, patch]
                if isinstance(min_engine_version_raw, str):
                    # Convert string like "1.21.30" to [1, 21, 30]
                    min_engine_version = [int(x) for x in min_engine_version_raw.split('.')]
                elif isinstance(min_engine_version_raw, list):
                    # Already a list, make a copy
                    min_engine_version = list(min_engine_version_raw)
                else:
                    # Try to convert to list
                    min_engine_version = [int(x) for x in str(min_engine_version_raw).split('.')]

                # Ensure version is a 3-part list (pad if necessary)
                while len(min_engine_version) < 3:
                    min_engine_version.append(0)

                # Determine if it's a resource pack or behavior pack
                if 'modules' in manifest_data:
                    for module in manifest_data['modules']:
                        if module['type'] == 'resources':
                            # Compare versions properly: [major, minor, patch]
                            if (highest_rp_version is None or
                                min_engine_version[0] > highest_rp_version[0] or
                                (min_engine_version[0] == highest_rp_version[0] and min_engine_version[1] > highest_rp_version[1]) or
                                (min_engine_version[0] == highest_rp_version[0] and min_engine_version[1] == highest_rp_version[1] and min_engine_version[2] > highest_rp_version[2])):
                                highest_rp_version = min_engine_version
                        elif module['type'] == 'data':
                            # Compare versions properly: [major, minor, patch]
                            if (highest_bp_version is None or
                                min_engine_version[0] > highest_bp_version[0] or
                                (min_engine_version[0] == highest_bp_version[0] and min_engine_version[1] > highest_bp_version[1]) or
                                (min_engine_version[0] == highest_bp_version[0] and min_engine_version[1] == highest_bp_version[1] and min_engine_version[2] > highest_bp_version[2])):
                                highest_bp_version = min_engine_version

                # Extract the dependencies if they exist
                if 'dependencies' in manifest_data:
                    for dependency in manifest_data['dependencies']:
                        module_name = dependency.get('module_name')
                        version = dependency.get('version')

                        if version:
                            # Store the full version (including any '-beta') for later use in manifest
                            version_full = version

                            # Extract only the numeric part for comparison (ignore '-beta' unless specified)
                            if isinstance(version, list):
                                version_numeric_parts = [int(v) for v in version]
                            else:
                                version_numeric_parts = [int(v.split('-')[0]) for v in str(version).split('.')]
                            while len(version_numeric_parts) < 3:
                                version_numeric_parts.append(0)

                            # Compare and update highest versions for dependencies
                            if module_name == "@minecraft/server":
                                if not highest_server_version or version_numeric_parts > highest_server_version:
                                    highest_server_version = version_numeric_parts
                                    highest_server_version_full = version_full  # Keep '-beta' for highest version
                            elif module_name == "@minecraft/server-ui":
                                if not highest_server_ui_version or version_numeric_parts > highest_server_ui_version:
                                    highest_server_ui_version = version_numeric_parts
                                    highest_server_ui_version_full = version_full  # Keep '-beta' for highest version
                            elif module_name == "@minecraft/server-gametest":
                                if not highest_gametest_version or version_numeric_parts > highest_gametest_version:
                                    highest_gametest_version = version_numeric_parts
                                    highest_gametest_version_full = version_full  # Keep '-beta' for highest version

                # Determine section based on min_engine_version
                if min_engine_version[0] == 1:
                    if min_engine_version[1] >= 21:
                        section = "These Addons Are Using 1.21+ Codes"
                    elif min_engine_version[1] == 20:
                        section = "These Addons Are Using 1.20+ Codes"
                    elif min_engine_version[1] == 19:
                        section = "These Addons Are Using 1.19+ Codes"
                    elif min_engine_version[1] == 18:
                        section = "These Addons Are Using 1.18+ Codes"
                    elif min_engine_version[1] == 17:
                        section = "These Addons Are Using 1.17+ Codes"
                    else:
                        section = "These Addons Are Using '1.16 And Below' Codes"
                else:
                    section = "These Addons Are Using '1.16 And Below' Codes"

                sections[section].append(f"{mcpack_name} (Version: {'.'.join(map(str, min_engine_version))})")

        # Set defaults if no versions were found
        if highest_server_version is None:
            highest_server_version = [1, 13, 0]
            highest_server_version_full = "1.13.0"
        if highest_server_ui_version is None:
            highest_server_ui_version = [1, 2, 0]
            highest_server_ui_version_full = "1.2.0"

        # Store the highest versions for later use in manifest creation
        self.highest_rp_version = highest_rp_version
        self.highest_bp_version = highest_bp_version
        self.highest_server_version_full = highest_server_version_full
        self.highest_server_ui_version_full = highest_server_ui_version_full
        self.highest_gametest_version_full = highest_gametest_version_full
        
    def _get_pack_script_api_version(self, manifest_data):
        """Return the script API version string from manifest dependencies (e.g. '1.8.0', '2.5.0', '1.2.0-beta'), or None."""
        if not manifest_data or 'dependencies' not in manifest_data:
            return None
        modules = manifest_data.get('modules') or []
        if isinstance(modules, list) and len(modules) > 0:
            first = modules[0] if isinstance(modules[0], dict) else {}
            if first.get('type') == 'resources':
                return None
        def _ver_tuple(v):
            """Convert '1.19.0-beta' → (1, 19, 0, 0) for numeric comparison."""
            try:
                clean = str(v).strip().lower().replace('-beta', '.1').replace('-', '.')
                parts = clean.split('.')
                return tuple(int(p) if p.isdigit() else 0 for p in parts[:4])
            except Exception:
                return (0, 0, 0, 0)

        version_str = None
        version_tup = (0, 0, 0, 0)
        for dep in manifest_data.get('dependencies') or []:
            if not isinstance(dep, dict):
                continue
            name = dep.get('module_name')
            if name in ('@minecraft/server', '@minecraft/server-ui', '@minecraft/server-gametest'):
                v = dep.get('version')
                if v:
                    vt = _ver_tuple(v)
                    if version_str is None or vt > version_tup:
                        version_str = str(v).strip()
                        version_tup = vt
        return version_str or None

    def _script_api_version_sort_key(self, v):
        """Sort key for version strings: newest first; 'none' last."""
        if v == 'none' or v is None:
            return (0, 0, 0, 0, 1)
        s = v.lower().replace('-beta', '')
        parts = s.split('.')
        try:
            major = int(parts[0]) if len(parts) > 0 else 0
            minor = int(parts[1]) if len(parts) > 1 else 0
            patch = int(parts[2]) if len(parts) > 2 else 0
            is_beta = 'beta' in v.lower()
            return (-major, -minor, -patch, 1 if is_beta else 0, 0)
        except (ValueError, IndexError):
            return (0, 0, 0, 0, 0)

    def _compute_script_api_groups(self):
        """Group pack names by the exact script API version found. Ignores resource packs (RPs don't use scripts). Returns (groups_dict, can_merge)."""
        groups = {}
        for _file in self._files:
            manifest_data = self._get_manifest_data(_file)
            if not manifest_data:
                continue
            modules = manifest_data.get('modules') or []
            if isinstance(modules, list) and len(modules) > 0:
                first = modules[0] if isinstance(modules[0], dict) else {}
                if first.get('type') == 'resources':
                    continue
            name = _os.path.basename(_file)
            ver = self._get_pack_script_api_version(manifest_data)
            key = ver if ver else 'none'
            if key not in groups:
                groups[key] = []
            groups[key].append(name)
        script_keys = [k for k in groups if k != 'none' and groups[k]]
        can_merge = len(script_keys) <= 1
        return groups, can_merge

    def _show_script_api_overlay(self, groups, can_merge):
        """Show in-app overlay: script API groups by found version and can/cannot merge."""
        for widget in self._script_api_overlay.winfo_children():
            widget.destroy()
        self._script_api_overlay.grid_columnconfigure(0, weight=1)
        self._script_api_overlay.grid_rowconfigure(0, weight=1)
        main = _tk.Frame(self._script_api_overlay, bg='#0f1419')
        main.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(0, weight=1)
        card = _tk.Frame(main, bg='#1a1a1a', relief='flat', bd=0)
        card.grid(row=0, column=0, sticky="nsew")
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(1, weight=1)
        _tk.Frame(card, bg='#9333ea', height=3).grid(row=0, column=0, sticky="ew")
        inner = _tk.Frame(card, bg='#1a1a1a')
        inner.grid(row=1, column=0, sticky="nsew", padx=40, pady=30)
        inner.grid_columnconfigure(0, weight=1)
        inner.grid_rowconfigure(3, weight=1)
        _tk.Label(inner, text="📜 " + _("script_api.title"), bg='#1a1a1a', fg='#FFFFFF',
                  font=('Segoe UI', 18, 'bold')).grid(row=0, column=0, pady=(0, 6), sticky="w")
        if can_merge:
            status_text = "✅ Same script API version — these packs can be merged together."
            status_fg = '#10b981'
        else:
            status_text = "❌ Different script API versions — do not merge these together (mixing versions will break scripts)."
            status_fg = '#ef4444'
        _tk.Label(inner, text=status_text, bg='#1a1a1a', fg=status_fg, font=('Segoe UI', 11),
                  wraplength=1200, justify='left').grid(row=1, column=0, pady=(0, 10), sticky="w")

        # Color legend
        legend_frame = _tk.Frame(inner, bg='#111111', highlightthickness=1, highlightbackground='#2d2d2d')
        legend_frame.grid(row=2, column=0, pady=(0, 16), sticky='w')
        _tk.Label(legend_frame, text='  Color key:', bg='#111111', fg='#999999',
                  font=('Segoe UI', 9, 'bold')).pack(side='left', padx=(8, 6), pady=6)
        for dot_col, dot_label in [
            ('#a78bfa', 'Script API v2.x'),
            ('#60a5fa', 'Script API v1.x'),
            ('#f59e0b', 'Beta version'),
            ('#6b7280', 'No script'),
        ]:
            swatch = _tk.Frame(legend_frame, bg=dot_col, width=10, height=10)
            swatch.pack(side='left', padx=(6, 2))
            swatch.pack_propagate(False)
            _tk.Label(legend_frame, text=dot_label, bg='#111111', fg='#d1d5db',
                      font=('Segoe UI', 9)).pack(side='left', padx=(0, 10), pady=6)

        canvas_container = _tk.Frame(inner, bg='#1a1a1a')
        canvas_container.grid(row=3, column=0, sticky="nsew")
        canvas_container.grid_columnconfigure(0, weight=1)
        canvas_container.grid_rowconfigure(0, weight=1)
        canvas = _tk.Canvas(canvas_container, bg='#1a1a1a', highlightthickness=0)
        scrollable = _tk.Frame(canvas, bg='#1a1a1a')

        def _update_scroll(event=None):
            canvas.update_idletasks()
            canvas.configure(scrollregion=canvas.bbox("all"))

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def _scroll_bind_enter(event):
            canvas_container.bind_all("<MouseWheel>", _on_mousewheel)

        def _scroll_bind_leave(event):
            canvas_container.unbind_all("<MouseWheel>")

        def _color_for_version(key):
            if key == 'none':
                return '#6b7280'
            if 'beta' in key.lower():
                return '#f59e0b'
            try:
                major = int(key.split('.')[0])
                return '#a78bfa' if major >= 2 else '#60a5fa'
            except (ValueError, IndexError):
                return '#9333ea'

        scrollable.bind("<Configure>", _update_scroll)
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas.find_all()[0], width=e.width) if canvas.find_all() else None)
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas_container.bind("<Enter>", _scroll_bind_enter)
        canvas_container.bind("<Leave>", _scroll_bind_leave)
        canvas.bind("<Enter>", _scroll_bind_enter)
        scrollable.bind("<Enter>", _scroll_bind_enter)
        row_num = 0
        sorted_keys = sorted(groups.keys(), key=self._script_api_version_sort_key)
        for key in sorted_keys:
            pack_list = sorted(groups[key])
            if not pack_list:
                continue
            if key == 'none':
                title = "No script dependencies"
            else:
                title = f"Script API @minecraft/server {key}"
            color = _color_for_version(key)
            header = _tk.Frame(scrollable, bg=color, height=42)
            header.grid(row=row_num, column=0, sticky="ew", padx=0, pady=(0, 0))
            header.grid_columnconfigure(0, weight=1)
            _tk.Label(header, text=f"  {title}  ·  {len(pack_list)} pack{'s' if len(pack_list) != 1 else ''}  ",
                     bg=color, fg='#FFFFFF', font=('Segoe UI', 12, 'bold'), anchor='w').grid(row=0, column=0, padx=20, pady=10, sticky="w")
            row_num += 1
            for pack_name in pack_list:
                display = (pack_name[:80] + "…") if len(pack_name) > 80 else pack_name
                rf = _tk.Frame(scrollable, bg='#1a1a1a', height=36)
                rf.grid(row=row_num, column=0, sticky="ew", padx=20, pady=2)
                rf.grid_columnconfigure(0, weight=1)
                _tk.Label(rf, text=display, bg='#1a1a1a', fg='#e5e7eb', font=('Segoe UI', 11), anchor='w').grid(row=0, column=0, padx=24, pady=8, sticky="w")
                row_num += 1
            row_num += 6
        scrollable.grid_columnconfigure(0, weight=1)
        canvas.grid(row=0, column=0, sticky="nsew")
        def _close_overlay():
            self._script_api_overlay.grid_remove()
            try:
                self._root.state('normal')
            except Exception:
                pass

        _tk.Button(inner, text=_("common.close"), command=_close_overlay,
                  bg='#9333ea', fg='#FFFFFF', font=('Segoe UI', 11, 'bold'), relief='flat', cursor='hand2',
                  activebackground='#a855f7', padx=30, pady=10).grid(row=4, column=0, pady=(15, 0))
        self._root.after(100, _update_scroll)
        self._script_api_overlay.grid()
        self._script_api_overlay.lift()
        try:
            self._root.state('zoomed')
        except Exception:
            pass

    def _show_conflict_resolution_overlay(self, conflict_list, identifier_manager, done_event):
        """Show overlay listing identifier conflicts; user chooses which pack to keep (or keep all). Blocks until Continue."""
        for w in self._conflict_resolution_overlay.winfo_children():
            w.destroy()
        self._conflict_resolution_overlay.grid_columnconfigure(0, weight=1)
        self._conflict_resolution_overlay.grid_rowconfigure(0, weight=1)
        main = _tk.Frame(self._conflict_resolution_overlay, bg='#0f1419')
        main.grid(row=0, column=0, sticky='nsew', padx=20, pady=20)
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(1, weight=1)
        card = _tk.Frame(main, bg='#1a1a1a', relief='flat')
        card.grid(row=0, column=0, sticky='nsew')
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(1, weight=1)
        _tk.Frame(card, bg='#9333ea', height=3).grid(row=0, column=0, sticky='ew')
        inner = _tk.Frame(card, bg='#1a1a1a')
        inner.grid(row=1, column=0, sticky='nsew', padx=40, pady=30)
        inner.grid_columnconfigure(0, weight=1)
        inner.grid_rowconfigure(2, weight=1)
        title = _("conflict.title") if _("conflict.title") != "conflict.title" else "Identifier conflicts"
        _tk.Label(inner, text="⚔ " + title, bg='#1a1a1a', fg='#FFFFFF', font=('Segoe UI', 18, 'bold')).grid(row=0, column=0, pady=(0, 6), sticky='w')
        desc = _("conflict.desc") if _("conflict.desc") != "conflict.desc" else "Choose which pack to keep for each conflicted identifier, or keep all (prefix)."
        _tk.Label(inner, text=desc, bg='#1a1a1a', fg='#E5E7EB', font=('Segoe UI', 11), wraplength=700, justify='left').grid(row=1, column=0, pady=(0, 16), sticky='w')
        canvas_container = _tk.Frame(inner, bg='#1a1a1a')
        canvas_container.grid(row=2, column=0, sticky='nsew')
        canvas_container.grid_columnconfigure(0, weight=1)
        canvas_container.grid_rowconfigure(0, weight=1)
        canvas = _tk.Canvas(canvas_container, bg='#1a1a1a', highlightthickness=0)
        scrollable = _tk.Frame(canvas, bg='#1a1a1a')
        row_vars = []

        def _update_scroll(_e=None):
            canvas.update_idletasks()
            canvas.configure(scrollregion=canvas.bbox('all'))

        def _on_wheel(e):
            canvas.yview_scroll(int(-1 * (e.delta / 120)), 'units')

        def _scroll_enter(e):
            canvas.bind_all('<MouseWheel>', _on_wheel)

        def _scroll_leave(e):
            try:
                canvas.unbind_all('<MouseWheel>')
            except Exception:
                pass

        scrollable.bind('<Configure>', _update_scroll)
        canvas.create_window((0, 0), window=scrollable, anchor='nw')
        canvas_container.bind('<Enter>', _scroll_enter)
        canvas_container.bind('<Leave>', _scroll_leave)
        canvas.bind('<Enter>', _scroll_enter)
        scrollable.bind('<Enter>', _scroll_enter)
        keep_all_label = "Merge All (combine)"
        for idx, (identifier, pack_paths) in enumerate(conflict_list):
            row = _tk.Frame(scrollable, bg='#252525', height=44)
            row.grid(row=idx, column=0, sticky='ew', padx=0, pady=2)
            row.grid_columnconfigure(0, weight=1)
            id_short = (identifier[:52] + "…") if len(identifier) > 52 else identifier
            _tk.Label(row, text=id_short, bg='#252525', fg='#E5E7EB', font=('Segoe UI', 10), anchor='w').grid(row=0, column=0, padx=12, pady=8, sticky='w')
            choices = [(_os.path.basename(p).replace('.mcpack', '').replace('.mcaddon', '').replace('_modified', ''), p) for p in pack_paths]
            display_choices = [keep_all_label] + [c[0] for c in choices]
            var = _tk.StringVar(self._root, value=keep_all_label)
            row_vars.append((identifier, pack_paths, choices, var))
            om = _tk.OptionMenu(row, var, keep_all_label, *[c[0] for c in choices])
            om.config(bg='#9333ea', fg='#FFFFFF', font=('Segoe UI', 10), anchor='w', relief='flat')
            om.grid(row=0, column=1, padx=12, pady=6)
        scrollable.grid_columnconfigure(0, weight=1)
        canvas.grid(row=0, column=0, sticky='nsew')

        def _on_continue():
            for identifier, pack_paths, choices, var in row_vars:
                val = var.get()
                if val == keep_all_label:
                    identifier_manager.set_user_resolution(identifier, None)
                else:
                    for disp, path in choices:
                        if val == disp:
                            identifier_manager.set_user_resolution(identifier, path)
                            break
            self._conflict_resolution_overlay.grid_remove()
            done_event.set()

        btn_row = _tk.Frame(inner, bg='#1a1a1a')
        btn_row.grid(row=3, column=0, pady=(16, 0))
        btn_text = _("conflict.continue") if _("conflict.continue") != "conflict.continue" else "Continue"
        _tk.Button(btn_row, text=btn_text, command=_on_continue, bg='#9333ea', fg='#FFFFFF', font=('Segoe UI', 11, 'bold'),
                  relief='flat', cursor='hand2', activebackground='#a855f7', padx=30, pady=10).pack(side='left')
        self._root.after(100, _update_scroll)
        self._conflict_resolution_overlay.grid()
        self._conflict_resolution_overlay.lift()

    def _extract_and_show_codes(self):
        """Check Packs: manifest check, obfuscation warning, and script API grouping (can/cannot merge)."""
        self._check_compatibility()
        if not self._files:
            _messagebox.showinfo(_("msg.error"), _("msg.no_mcpack_added"))
            return
        bad_packs = []
        for _file in self._files:
            if self._is_pack_obfuscated(_file):
                bad_packs.append(_os.path.basename(_file))
        if bad_packs:
            msg = "⚠ CRITICAL: CLOSED-SOURCE PACKS DETECTED\n\n"
            msg += "The following packs contain '*/' or Unicode-obfuscated JSON files. "
            msg += "Merging these WILL CORRUPT the final output and cause Minecraft to crash.\n\n"
            msg += "Please REMOVE these files from the list before merging:\n\n• "
            msg += "\n• ".join(bad_packs)
            _messagebox.showwarning("Corrupted Pack Warning", msg)
        else:
            groups, can_merge = self._compute_script_api_groups()
            self._show_script_api_overlay(groups, can_merge)

    def _show_version_check_overlay(self, pack_info_list):
        """Show a themed version check overlay that matches the tool's theme, grouped by version."""
        # Clear existing widgets in overlay
        for widget in self._version_check_overlay.winfo_children():
            widget.destroy()
        
        # Create a variable to track when overlay should close
        overlay_done = _tk.BooleanVar(self._root, False)
        
        # Configure overlay for proper resizing
        self._version_check_overlay.grid_columnconfigure(0, weight=1)
        self._version_check_overlay.grid_rowconfigure(0, weight=1)
        
        # Create main container that fills the overlay
        main_container = _tk.Frame(self._version_check_overlay, bg='#0f1419')
        main_container.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        main_container.grid_columnconfigure(0, weight=1)
        main_container.grid_rowconfigure(1, weight=1)
        
        # Card frame with proper sizing
        card_frame = _tk.Frame(main_container, bg='#1a1a1a', relief='flat', bd=0)
        card_frame.grid(row=0, column=0, sticky="nsew")
        card_frame.grid_columnconfigure(0, weight=1)
        card_frame.grid_rowconfigure(1, weight=1)
        
        # Card border
        border_frame = _tk.Frame(card_frame, bg='#9333ea', height=3)
        border_frame.grid(row=0, column=0, sticky="ew")
        
        # Inner container with proper padding
        inner_frame = _tk.Frame(card_frame, bg='#1a1a1a')
        inner_frame.grid(row=1, column=0, sticky="nsew", padx=25, pady=25)
        inner_frame.grid_columnconfigure(0, weight=1)
        inner_frame.grid_rowconfigure(2, weight=1)
        
        # Title
        title_label = _tk.Label(inner_frame, text="🔍 " + _("version_check.title"), 
                               bg='#1a1a1a', fg='#FFFFFF', 
                               font=('Segoe UI', 16, 'bold'))
        title_label.grid(row=0, column=0, pady=(0, 10), sticky="w")
        
        # Warning message
        warning_label = _tk.Label(inner_frame, 
                                text="⚠️ " + _("version_check.same_version_note"),
                                bg='#1a1a1a', fg='#ff6b6b', 
                                font=('Segoe UI', 10),
                                wraplength=700, justify='left')
        warning_label.grid(row=1, column=0, pady=(0, 15), sticky="w")
        
        if not pack_info_list:
            no_packs_label = _tk.Label(inner_frame, text=_("version_check.no_packs"),
                                      bg='#1a1a1a', fg='#999999', 
                                      font=('Segoe UI', 11))
            no_packs_label.grid(row=2, column=0, pady=20)
        else:
            # Group packs by version
            version_groups = {}
            for pack_info in pack_info_list:
                version = pack_info['version']
                if version not in version_groups:
                    version_groups[version] = []
                version_groups[version].append(pack_info)
            
            # Sort versions (newest first)
            sorted_versions = sorted(version_groups.keys(), reverse=True, 
                                    key=lambda v: tuple(map(int, v.split('.'))))
            
            # Create scrollable frame for categorized pack list
            canvas_container = _tk.Frame(inner_frame, bg='#1a1a1a')
            canvas_container.grid(row=2, column=0, sticky="nsew")
            canvas_container.grid_columnconfigure(0, weight=1)
            canvas_container.grid_rowconfigure(0, weight=1)
            
            canvas = _tk.Canvas(canvas_container, bg='#1a1a1a', highlightthickness=0)
            scrollbar = _tk.Scrollbar(canvas_container, orient='vertical', command=canvas.yview,
                                     bg='#0A0A0A', troughcolor='#1a1a1a',
                                     activebackground='#2d2d2d', width=15)
            scrollable_frame = _tk.Frame(canvas, bg='#1a1a1a')
            
            def update_scroll_region(event=None):
                canvas.update_idletasks()
                canvas.configure(scrollregion=canvas.bbox("all"))
            
            scrollable_frame.bind("<Configure>", update_scroll_region)
            canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas.find_all()[0], width=e.width))
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            # Display packs grouped by version
            row_num = 0
            for version in sorted_versions:
                packs_in_version = version_groups[version]
                count = len(packs_in_version)
                
                # Version category header
                version_header = _tk.Frame(scrollable_frame, bg='#9333ea', height=35)
                version_header.grid(row=row_num, column=0, sticky="ew", padx=0, pady=(0, 8))
                version_header.grid_columnconfigure(0, weight=1)
                
                version_text = f"Version {version} ({count} pack{'s' if count != 1 else ''}) - Safe to merge together"
                _tk.Label(version_header, text=version_text, bg='#9333ea', fg='#FFFFFF',
                         font=('Segoe UI', 12, 'bold'), anchor='w').grid(row=0, column=0, padx=15, pady=8, sticky="w")
                row_num += 1
                
                # Pack rows for this version
                for pack_info in packs_in_version:
                    row_frame = _tk.Frame(scrollable_frame, bg='#1a1a1a')
                    row_frame.grid(row=row_num, column=0, sticky="ew", padx=10, pady=3)
                    row_frame.grid_columnconfigure(0, weight=1)
                    
                    # Pack name (truncate if too long)
                    pack_name = pack_info['name']
                    if len(pack_name) > 50:
                        pack_name = pack_name[:47] + "..."
                    
                    name_label = _tk.Label(row_frame, text=pack_name, bg='#1a1a1a', fg='#FFFFFF',
                                         font=('Segoe UI', 10), anchor='w')
                    name_label.grid(row=0, column=0, padx=(15, 10), pady=6, sticky="ew")
                    
                    type_label = _tk.Label(row_frame, text=pack_info['type'], bg='#1a1a1a', fg='#60a5fa',
                                         font=('Segoe UI', 10))
                    type_label.grid(row=0, column=1, padx=10, pady=6, sticky="e")
                    
                    row_num += 1
            
            # Configure scrollable frame columns
            scrollable_frame.grid_columnconfigure(0, weight=1)
            scrollable_frame.grid_columnconfigure(1, weight=0)
            
            canvas.grid(row=0, column=0, sticky="nsew")
            scrollbar.grid(row=0, column=1, sticky="ns")
            
            # Make canvas expandable
            canvas_container.grid_rowconfigure(0, weight=1)
            canvas_container.grid_columnconfigure(0, weight=1)
        
        def on_close():
            overlay_done.set(True)
            self._version_check_overlay.grid_remove()
        
        # Close button
        button_frame = _tk.Frame(inner_frame, bg='#1a1a1a')
        button_frame.grid(row=3, column=0, pady=(15, 0))
        
        close_btn = _tk.Button(button_frame, text=_("common.close"), command=on_close,
                              bg='#9333ea', fg='#FFFFFF', 
                              font=('Segoe UI', 11, 'bold'),
                              relief='flat', cursor='hand2',
                              activebackground='#a855f7',
                              padx=30, pady=10)
        close_btn.pack()
        
        # Show overlay
        self._version_check_overlay.grid()
        self._version_check_overlay.lift()  # Bring to front
        
        # Update scroll region after a moment to ensure proper sizing
        self._root.after(100, update_scroll_region)
        
        # Wait for user to close
        self._root.wait_variable(overlay_done)

    def _show_version_message(self, sections):
        # Legacy function - kept for backward compatibility but not used
        # Prepare the message to display
        messages = []
        for section, items in sections.items():
            if items:
                messages.append(f"{section}:\n" + "\n".join([f"- {item}" for item in items]))

        if messages:
            warning_message = "Warning: Merging Addons With Different Codes Or format_version May Cause To Break Some Of The Addons' Features, Also Merging The Json UI And The Scripts May Not Be 100% Perfect."
            messages.append(warning_message)
            _messagebox.showinfo(_("addons_used.title"), "\n\n".join(messages))
        else:
            _messagebox.showinfo(_("addons_used.title"), _("version_check.no_packs"))
