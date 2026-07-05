class IdentifierManager:
    """
    Manages identifier conflicts by:
    1. Scanning all identifiers in packs
    2. Detecting conflicts
    3. Generating unique namespaces
    4. Prefixing identifiers
    5. Tracking and updating references
    """
    
    def __init__(self):
        self.all_identifiers = defaultdict(set)  # type -> set of identifiers
        self.pack_identifiers = {}  # pack_path -> {type -> set of identifiers}
        self.identifier_mapping = {}  # (pack_path, old_id) -> new_id
        self.pack_namespaces = {}  # pack_path -> namespace_prefix
        self.conflict_map = defaultdict(set)  # identifier -> {pack_paths}
        self.reference_files = defaultdict(set)  # identifier -> set of file_paths
        # User resolution: identifier -> pack_path to keep (None = keep all / prefix)
        self.user_resolution = {}
        
    def scan_pack_identifiers(self, pack_zip, pack_path):
        """
        Scan a pack for all identifiers (entities, items, blocks, loot tables, recipes).
        Returns dict of identifier types and their values.
        """
        identifiers = {
            'entities': set(),
            'items': set(),
            'blocks': set(),
            'loot_tables': set(),
            'recipes': set(),
            'animation_controllers': set(),
            'render_controllers': set(),
            'textures': set()
        }
        
        try:
            for item_name in pack_zip.namelist():
                if item_name.startswith('subpacks/'):
                    continue
                    
                # Scan entity files
                if item_name.startswith('entities/') and item_name.endswith('.json'):
                    identifiers['entities'].update(self._extract_entity_identifiers(pack_zip, item_name))
                    
                # Scan item files
                if item_name.startswith('items/') and item_name.endswith('.json'):
                    identifiers['items'].update(self._extract_item_identifiers(pack_zip, item_name))
                    
                # Scan block files
                if item_name.startswith('blocks/') and item_name.endswith('.json'):
                    identifiers['blocks'].update(self._extract_block_identifiers(pack_zip, item_name))
                    
                # Scan loot tables
                if item_name.startswith('loot_tables/') and item_name.endswith('.json'):
                    loot_id = self._extract_loot_table_id(item_name)
                    if loot_id:
                        identifiers['loot_tables'].add(loot_id)
                        
                # Scan recipes
                if item_name.startswith('recipes/') and item_name.endswith('.json'):
                    identifiers['recipes'].update(self._extract_recipe_identifiers(pack_zip, item_name))
                    
                # Scan animation controllers
                if 'animation_controllers' in item_name and item_name.endswith('.json'):
                    identifiers['animation_controllers'].update(self._extract_animation_controller_identifiers(pack_zip, item_name))
                    
                # Scan render controllers
                if 'render_controllers' in item_name and item_name.endswith('.json'):
                    identifiers['render_controllers'].update(self._extract_render_controller_identifiers(pack_zip, item_name))
                    
        except Exception as e:
            _logging.warning(f"Error scanning identifiers in {pack_path}: {e}")
            
        return identifiers
    
    def _extract_entity_identifiers(self, pack_zip, item_name):
        """Extract entity identifiers from entity JSON file."""
        identifiers = set()
        try:
            with pack_zip.open(item_name) as f:
                content = f.read().decode('utf-8', errors='ignore')
                # Remove comments
                content = _re.sub(r'//.*?$|/\*.*?\*/', '', content, flags=_re.MULTILINE | _re.DOTALL)
                try:
                    data = _json.loads(content)
                    # Check for minecraft:entity or minecraft:client_entity
                    for key in ['minecraft:entity', 'minecraft:client_entity']:
                        if key in data:
                            desc = data[key].get('description', {})
                            entity_id = desc.get('identifier')
                            if entity_id and entity_id != 'minecraft:player':
                                identifiers.add(entity_id)
                except:
                    pass
        except:
            pass
        return identifiers
    
    def _extract_item_identifiers(self, pack_zip, item_name):
        """Extract item identifiers from item JSON file."""
        identifiers = set()
        try:
            with pack_zip.open(item_name) as f:
                content = f.read().decode('utf-8', errors='ignore')
                content = _re.sub(r'//.*?$|/\*.*?\*/', '', content, flags=_re.MULTILINE | _re.DOTALL)
                try:
                    data = _json.loads(content)
                    if 'minecraft:item' in data:
                        desc = data['minecraft:item'].get('description', {})
                        item_id = desc.get('identifier')
                        if item_id:
                            identifiers.add(item_id)
                except:
                    pass
        except:
            pass
        return identifiers
    
    def _extract_block_identifiers(self, pack_zip, item_name):
        """Extract block identifiers from block JSON file."""
        identifiers = set()
        try:
            with pack_zip.open(item_name) as f:
                content = f.read().decode('utf-8', errors='ignore')
                content = _re.sub(r'//.*?$|/\*.*?\*/', '', content, flags=_re.MULTILINE | _re.DOTALL)
                try:
                    data = _json.loads(content)
                    if 'minecraft:block' in data:
                        desc = data['minecraft:block'].get('description', {})
                        block_id = desc.get('identifier')
                        if block_id:
                            identifiers.add(block_id)
                except:
                    pass
        except:
            pass
        return identifiers
    
    def _extract_loot_table_id(self, item_name):
        """Extract loot table identifier from file path."""
        # Format: loot_tables/entities/zombie.json -> minecraft:entities/zombie
        if item_name.startswith('loot_tables/'):
            path_part = item_name[12:]  # Remove 'loot_tables/'
            if path_part.endswith('.json'):
                path_part = path_part[:-5]  # Remove '.json'
                # Convert path to identifier format
                parts = path_part.split('/')
                if len(parts) >= 2:
                    return f"{parts[0]}:{'/'.join(parts[1:])}"
                elif len(parts) == 1:
                    return f"loot_tables:{parts[0]}"
        return None
    
    def _extract_recipe_identifiers(self, pack_zip, item_name):
        """Extract recipe identifiers from recipe JSON file."""
        identifiers = set()
        try:
            with pack_zip.open(item_name) as f:
                content = f.read().decode('utf-8', errors='ignore')
                content = _re.sub(r'//.*?$|/\*.*?\*/', '', content, flags=_re.MULTILINE | _re.DOTALL)
                try:
                    data = _json.loads(content)
                    # Recipes can have identifier in description or as key
                    if 'minecraft:recipe_furnace' in data or 'minecraft:recipe_shaped' in data or 'minecraft:recipe_shapeless' in data:
                        for key in data.keys():
                            if 'recipe' in key.lower():
                                recipe_data = data[key]
                                if isinstance(recipe_data, dict):
                                    desc = recipe_data.get('description', {})
                                    recipe_id = desc.get('identifier')
                                    if recipe_id:
                                        identifiers.add(recipe_id)
                except:
                    pass
        except:
            pass
        return identifiers
    
    def _extract_animation_controller_identifiers(self, pack_zip, item_name):
        """Extract animation controller identifiers."""
        identifiers = set()
        try:
            with pack_zip.open(item_name) as f:
                content = f.read().decode('utf-8', errors='ignore')
                content = _re.sub(r'//.*?$|/\*.*?\*/', '', content, flags=_re.MULTILINE | _re.DOTALL)
                try:
                    data = _json.loads(content)
                    # Animation controllers are keyed by identifier
                    for key in data.keys():
                        if ':' in key:  # Has namespace:name format
                            identifiers.add(key)
                except:
                    pass
        except:
            pass
        return identifiers
    
    def _extract_render_controller_identifiers(self, pack_zip, item_name):
        """Extract render controller identifiers."""
        identifiers = set()
        try:
            with pack_zip.open(item_name) as f:
                content = f.read().decode('utf-8', errors='ignore')
                content = _re.sub(r'//.*?$|/\*.*?\*/', '', content, flags=_re.MULTILINE | _re.DOTALL)
                try:
                    data = _json.loads(content)
                    # Render controllers are keyed by identifier
                    for key in data.keys():
                        if ':' in key:
                            identifiers.add(key)
                except:
                    pass
        except:
            pass
        return identifiers
    
    def detect_conflicts(self, all_pack_identifiers):
        """
        Detect identifier conflicts across all packs.
        all_pack_identifiers: dict of pack_path -> identifiers dict
        """
        # Aggregate all identifiers by type
        type_identifiers = defaultdict(set)
        self.pack_identifiers = all_pack_identifiers
        
        for pack_path, identifiers in all_pack_identifiers.items():
            for id_type, id_set in identifiers.items():
                type_identifiers[id_type].update(id_set)
                # Track which packs use each identifier
                for identifier in id_set:
                    # Skip the entire minecraft: namespace — those are vanilla entity/item/block
                    # modifications that should always be deep-merged, never renamed or flagged.
                    # Also skip loot_tables: — vanilla loot table references included by many packs.
                    ns = identifier.split(':')[0] if ':' in identifier else ''
                    if ns in ('minecraft', 'loot_tables'):
                        continue
                    self.conflict_map[identifier].add(pack_path)
        
        # Generate namespace prefixes for each pack
        for idx, pack_path in enumerate(all_pack_identifiers.keys()):
            # Create unique namespace prefix (pack1_merge, pack2_merge, etc.)
            pack_name = _os.path.basename(pack_path).replace('.mcpack', '').replace('.mcaddon', '')
            # Clean up pack name for namespace (only alphanumeric and underscore)
            clean_name = _re.sub(r'[^a-zA-Z0-9_]', '_', pack_name)[:20]
            self.pack_namespaces[pack_path] = f"{clean_name}_merge"
    
    @staticmethod
    def _pack_base_name(pack_path):
        """Strip AutoBE's internal suffixes so BP/RP halves of the same addon compare equal."""
        name = _os.path.basename(pack_path)
        name = _re.sub(r'\.(mcpack|mcaddon)$', '', name, flags=_re.IGNORECASE)
        # Strip _modified (subpack-extracted temp copy) then _N split suffix, in that order
        name = _re.sub(r'_modified$', '', name, flags=_re.IGNORECASE)
        name = _re.sub(r'_\d+$', '', name)
        # Strip common BP/RP halve suffixes so paired addon halves resolve to the same base name
        name = _re.sub(
            r'[_\-\s]*(bp|rp|behaviors?|resources?|behavior[_\-]?pack|resource[_\-]?pack)$',
            '', name, flags=_re.IGNORECASE)
        return name.lower()

    def get_conflict_list(self):
        """Return list of (identifier, list of pack_paths) for all conflicted identifiers.
        Excludes false conflicts where every involved pack is a BP/RP half of the same addon
        (identified by sharing the same base name after stripping AutoBE's _N split suffix)."""
        result = []
        for identifier, packs in self.conflict_map.items():
            if len(packs) <= 1:
                continue
            base_names = {self._pack_base_name(p) for p in packs}
            if len(base_names) == 1:
                # All packs are halves of the same addon — not a real conflict
                continue
            result.append((identifier, list(packs)))
        return result

    def set_user_resolution(self, identifier, pack_path_or_none):
        """Set user choice for a conflicted identifier: pack_path to keep, or None to keep all (prefix)."""
        self.user_resolution[identifier] = pack_path_or_none

    def should_include_definition(self, pack_path, identifier):
        """Return True if this pack's definition of the identifier should be included in the merge.
        If user chose to keep one pack only, other packs' definitions are excluded."""
        if identifier not in self.user_resolution:
            return True
        keep = self.user_resolution[identifier]
        if keep is None:
            return True
        return pack_path == keep

    def generate_identifier_mappings(self):
        """
        Generate identifier mappings.
        'Keep all' (default/None) = no renaming; the entity/item/block merge system
        combines definitions naturally so identifiers stay intact and all references work.
        Only 'Keep one pack' (explicit pack_path) generates a mapping entry (to filter others).
        """
        conflicted_identifiers = {id: packs for id, packs in self.conflict_map.items() if len(packs) > 1}

        for identifier, pack_paths in conflicted_identifiers.items():
            keep_pack = self.user_resolution.get(identifier)
            if keep_pack is not None:
                # User explicitly chose one pack — all packs map to the original id
                # (filtering is handled by should_include_definition; the winner keeps its id)
                for pack_path in pack_paths:
                    self.identifier_mapping[(pack_path, identifier)] = identifier
            # 'Keep all' (keep_pack is None): no rename mapping created.
            # All packs' definitions pass through; the merge system deep-merges them
            # under the original identifier so every reference in every file stays valid.

        _logging.info(f"Generated {len(self.identifier_mapping)} identifier mappings (renaming disabled for merge mode)")
    
    def get_new_identifier(self, pack_path, old_identifier):
        """Get the new identifier for a given pack and old identifier."""
        return self.identifier_mapping.get((pack_path, old_identifier), old_identifier)
    
    def should_rename_identifier(self, identifier):
        """Check if an identifier needs to be renamed (has conflicts)."""
        return len(self.conflict_map.get(identifier, [])) > 1
    
    def update_json_identifiers(self, json_data, pack_path):
        """
        Recursively update all identifier references in JSON data.
        Returns updated JSON data structure.
        """
        if isinstance(json_data, dict):
            updated = {}
            for key, value in json_data.items():
                # Update identifier fields
                if key == 'identifier' and isinstance(value, str):
                    updated[key] = self.get_new_identifier(pack_path, value)
                elif key in ['entity', 'item', 'block', 'loot_table', 'recipe'] and isinstance(value, str):
                    # Update references to entities/items/blocks
                    updated[key] = self.get_new_identifier(pack_path, value)
                else:
                    # Recursively update nested structures
                    updated[key] = self.update_json_identifiers(value, pack_path)
            return updated
        elif isinstance(json_data, list):
            return [self.update_json_identifiers(item, pack_path) for item in json_data]
        elif isinstance(json_data, str):
            # Check if string is an identifier reference (contains :)
            if ':' in json_data and not json_data.startswith('http'):
                # Try to update if it matches a known identifier
                new_id = self.get_new_identifier(pack_path, json_data)
                return new_id
        return json_data
    
    def update_text_identifiers(self, text, pack_path):
        """
        Update identifier references in text content (scripts, lang files, etc.).
        Uses regex to find and replace identifier patterns.
        """
        # Pattern to match identifiers (namespace:name format)
        identifier_pattern = r'\b([a-zA-Z0-9_]+:[a-zA-Z0-9_\./]+)\b'
        
        def replace_identifier(match):
            old_id = match.group(1)
            new_id = self.get_new_identifier(pack_path, old_id)
            return new_id
        
        updated_text = _re.sub(identifier_pattern, replace_identifier, text)
        return updated_text

def find_valid_packs(entry, max_depth=10):
    """
    Recursively find all pack folders (manifest.json at root) inside entry.
    Returns a list of absolute paths to valid pack folders.
    """
    found = []
    if max_depth < 1:
        return []
    if _os.path.isdir(entry):
        if _os.path.isfile(_os.path.join(entry, 'manifest.json')):
            found.append(entry)
            return found
        for child in _os.listdir(entry):
            child_path = _os.path.join(entry, child)
            found += find_valid_packs(child_path, max_depth-1)
        return found
    ext = _os.path.splitext(entry)[1].lower()
    if ext in ('.mcpack', '.mcaddon', '.zip'):
        tempdir = _tempfile.mkdtemp(prefix='mcpacker_temp_')
        try:
            with _zipfile.ZipFile(entry, 'r') as z:
                z.extractall(tempdir)
            for item in _os.listdir(tempdir):
                child_path = _os.path.join(tempdir, item)
                found += find_valid_packs(child_path, max_depth-1)
            if _os.path.isfile(_os.path.join(tempdir, 'manifest.json')):
                found.append(tempdir)
        except Exception as e:
            print(f"Failed to unzip {entry}: {e}")
        # Don't delete tempdir here! (wait until after zipping result)
    return found

def zip_pack_folder(folder, output_mcpack_path):
    with _zipfile.ZipFile(output_mcpack_path, 'w', _zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in _os.walk(folder):
            rel = _os.path.relpath(root, folder)
            for file in files:
                abs_path = _os.path.join(root, file)
                arcname = _os.path.join(rel, file) if rel != '.' else file
                zf.write(abs_path, arcname)

def safe_decode(byte_data):
    try:
        return byte_data.decode('utf-8')
    except UnicodeDecodeError:
        return byte_data.decode('latin-1')

class _T1:
    def __init__(self, _p1):
        self._p1 = _p1
        self._agreed = False  # True only after user clicks Agree
        self._terms_scrolled_to_bottom = False
        self._drag_offset_x = 0
        self._drag_offset_y = 0
        self._w1 = _tk.Toplevel(_p1)
        _apply_window_icon_global(self._w1)
        self._w1.title(_("tos.window_title"))
        self._w1.geometry("840x620")
        self._w1.configure(bg='#000000')
        self._w1.overrideredirect(True)
        # Single taskbar fix attempt to show icon in taskbar
        self._w1.after(100, lambda: _force_taskbar_button(self._w1))
        self._w1.grid_columnconfigure(0, weight=1)
        self._w1.grid_rowconfigure(0, weight=0)
        self._w1.grid_rowconfigure(1, weight=1)
        self._w1.grid_rowconfigure(2, weight=0)
        # If user closes via X instead of Agree, exit the app (must agree to use)
        self._w1.protocol("WM_DELETE_WINDOW", self._on_close_x)

        # Custom dark title bar (guaranteed black style)
        titlebar = _tk.Frame(self._w1, bg="#000000", height=36, highlightthickness=1, highlightbackground="#1f1f1f")
        titlebar.grid(row=0, column=0, sticky="ew")
        titlebar.grid_columnconfigure(1, weight=1)
        titlebar.grid_propagate(False)
        self._tos_title_icon_img = _get_titlebar_icon_image(14)
        if self._tos_title_icon_img is not None:
            title_icon = _tk.Label(titlebar, image=self._tos_title_icon_img, bg="#000000")
        else:
            title_icon = _tk.Label(titlebar, text="◈", bg="#000000", fg="#9333ea", font=("Segoe UI", 10, "bold"))
        title_icon.grid(row=0, column=0, padx=(10, 6), sticky="w")
        title_lbl = _tk.Label(titlebar, text=_("tos.window_title"), bg="#000000", fg="#E5E7EB", font=("Segoe UI", 10))
        title_lbl.grid(row=0, column=1, padx=(0, 6), sticky="w")
        close_btn = _tk.Button(titlebar, text="✕", command=self._on_close_x, bg="#000000", fg="#E5E7EB",
                               font=("Segoe UI", 10, "bold"), relief="flat", bd=0, padx=12, pady=3,
                               activebackground="#c42b1c", activeforeground="#FFFFFF", cursor="hand2")
        close_btn.grid(row=0, column=2, sticky="e")
        for w in (titlebar, title_icon, title_lbl):
            w.bind("<ButtonPress-1>", self._drag_start, add="+")
            w.bind("<B1-Motion>", self._drag_move, add="+")

        # Main container
        container = _tk.Frame(self._w1, bg='#000000')
        container.grid(row=1, column=0, sticky="nsew", padx=16, pady=(12, 8))
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(1, weight=1)

        self._tos_hint_label = _tk.Label(
            container,
            text="Read and scroll to the bottom to enable Agree.",
            bg="#000000",
            fg="#9CA3AF",
            font=("Segoe UI", 10),
        )
        self._tos_hint_label.grid(row=0, column=0, sticky="w", pady=(0, 8))

        # Terms body
        self._t1 = _tk.Text(
            container,
            wrap=_tk.WORD,
            bg='#0A0A0A',
            fg='#FFFFFF',
            font=("Segoe UI", 11),
            insertbackground='#a855f7',
            relief='flat',
            bd=0,
            padx=12,
            pady=10,
        )
        self._t1.grid(row=1, column=0, sticky="nsew")
        self._t1.bind("<MouseWheel>", self._on_terms_mousewheel, add="+")
        self._t1.bind("<Button-4>", self._on_terms_mousewheel, add="+")
        self._t1.bind("<Button-5>", self._on_terms_mousewheel, add="+")
        self._t1.bind("<Configure>", lambda _e: self._check_terms_scrolled_to_bottom(), add="+")

        _terms_text = _get_tos_text() or ("SOFTWARE LICENSE AGREEMENT\n\n" + _("tos.window_title"))
        self._t1.insert(_tk.END, _terms_text)
        self._t1.config(state=_tk.DISABLED)

        # Footer actions
        button_frame = _tk.Frame(self._w1, bg='#000000')
        button_frame.grid(row=2, column=0, sticky="ew", padx=16, pady=(4, 14))
        button_frame.grid_columnconfigure(0, weight=1)

        action_frame = _tk.Frame(button_frame, bg="#000000")
        action_frame.grid(row=0, column=1, sticky="e")

        self._decline_btn = _tk.Button(
            action_frame,
            text="✕ Decline",
            command=self._on_close_x,
            bg="#1f1f1f",
            fg="#FFFFFF",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            cursor="hand2",
            activebackground="#2d2d2d",
            padx=16,
            pady=8,
        )
        self._decline_btn.pack(side=_tk.LEFT, padx=(0, 10))

        self._b1 = _tk.Button(
            action_frame,
            text="✓ " + _("activation.i_agree") + " (scroll to bottom)",
            command=self._accept,
            bg="#3a3a3a",
            fg="#8f8f8f",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            cursor="arrow",
            activebackground="#3a3a3a",
            activeforeground="#8f8f8f",
            disabledforeground="#8f8f8f",
            state=_tk.DISABLED,
            padx=16,
            pady=8,
        )
        self._b1.pack(side=_tk.LEFT)
        self._w1.after(50, self._check_terms_scrolled_to_bottom)

    def _drag_start(self, event):
        self._drag_offset_x = event.x_root - self._w1.winfo_x()
        self._drag_offset_y = event.y_root - self._w1.winfo_y()

    def _drag_move(self, event):
        x = event.x_root - self._drag_offset_x
        y = event.y_root - self._drag_offset_y
        self._w1.geometry(f"+{x}+{y}")

    def _on_terms_mousewheel(self, event):
        try:
            if getattr(event, "num", None) == 4:
                self._t1.yview_scroll(-3, "units")
            elif getattr(event, "num", None) == 5:
                self._t1.yview_scroll(3, "units")
            else:
                delta = int(getattr(event, "delta", 0))
                if delta != 0:
                    # Windows/macOS wheel delta handling.
                    self._t1.yview_scroll(int(-delta / 120) * 3, "units")
            self._check_terms_scrolled_to_bottom()
        except Exception:
            pass
        return "break"

    def _check_terms_scrolled_to_bottom(self):
        if self._terms_scrolled_to_bottom:
            return
        try:
            _first, last = self._t1.yview()
            # Lower threshold to 0.95 to account for text widget padding and rendering differences
            if float(last) >= 0.95:
                self._terms_scrolled_to_bottom = True
                self._tos_hint_label.config(text="You reached the end. You can now agree.", fg="#C4B5FD")
                self._b1.config(
                    state=_tk.NORMAL,
                    text="✓ " + _("activation.i_agree"),
                    bg="#9333ea",
                    fg="#FFFFFF",
                    activebackground="#a855f7",
                    activeforeground="#FFFFFF",
                    cursor="hand2",
                )
        except Exception:
            pass

    def _accept(self):
        if not self._terms_scrolled_to_bottom:
            _messagebox.showinfo(
                _("tos.window_title"),
                "Please scroll to the bottom of the terms before accepting.",
            )
            return
        self._agreed = True
        # Smooth transition: withdraw TOS window first
        self._w1.withdraw()
        self._w1.update_idletasks()
        # Destroy TOS window after transition
        self._w1.after(50, self._w1.destroy)
        # Show main window smoothly
        self._p1.deiconify()
        self._p1.lift()
        self._p1.focus_force()
        self._p1.update_idletasks()
        # Apply taskbar fixes with minimal delay to reduce flickering
        self._p1.after(150, lambda: _force_taskbar_button(self._p1))
        self._p1.after(300, lambda: _apply_window_icon(self._p1))

    def _on_close_x(self):
        """User closed terms window without agreeing; close the app. Do nothing if they clicked Agree (destroy can trigger this)."""
        if self._agreed:
            return
        try:
            self._w1.destroy()
        except Exception:
            pass
        try:
            self._p1.destroy()
        except Exception:
            pass
        _os._exit(0)

class _ActivationWindow:
    def __init__(self, _p1):
        self._p1 = _p1
        self._w1 = _tk.Toplevel(_p1)
        _apply_window_icon_global(self._w1)
        self._w1.title("Enter Activation Key")
        self._w1.geometry("400x200")
        self._w1.configure(bg='#0A0A0A')

        self._label = _tk.Label(self._w1, text=_("activation.enter_key"), bg='#0A0A0A', fg='#E1E1E1', font=("Helvetica", 12))
        self._label.pack(pady=10)

        self._entry_key = _tk.Entry(self._w1, width=40, bg='#1A1A1A', fg='#A50CAC', font=("Helvetica", 12))
        self._entry_key.pack(pady=10)

        self._btn_submit = _tk.Button(self._w1, text=_("activation.submit"), command=self._submit_key, bg='#A50CAC', fg='#FFFFFF', font=("Helvetica", 12, "bold"))
        self._btn_submit.pack(pady=10)

    def _fetch_github_file(self, file_path):
        """Fetch a file from GitHub using the API with token. Returns None if network/DNS fails (offline)."""
        _headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        api_url = f"https://api.github.com/repos/FrostyHostMC/AutoBE/contents/{file_path}"
        try:
            response = _requests.get(api_url, headers=_headers, timeout=10)
            response.raise_for_status()
            file_data = response.json()
            content = base64.b64decode(file_data['content']).decode('utf-8')
            return content
        except (_requests.exceptions.ConnectionError, _requests.exceptions.Timeout, _requests.exceptions.HTTPError, OSError) as e:
            _logging.debug("GitHub fetch failed (network/HTTP error): %s", e)
            return None
        except Exception:
            raise

    def _submit_key(self):
        _key = self._entry_key.get().strip()

        if not _key:
            _messagebox.showerror(_("msg.error"), _("activation.enter_key_error"))
            return

        try:
            # Fetch the current list of valid keys using the helper function
            keys_text = self._fetch_github_file("keys.csv")
            if keys_text is None:
                _messagebox.showerror(_("msg.error"), _("msg.connection_error") if _("msg.connection_error") != "msg.connection_error" else "Cannot reach server. Check your internet connection and try again.")
                return
            response_text = keys_text

            # Parse CSV - try multiple methods to handle various formats
            valid_keys = []
            
            # Method 1: Try CSV reader (handles quoted values)
            try:
                csv_reader = csv.reader(io.StringIO(response_text), quoting=csv.QUOTE_MINIMAL)
                for row in csv_reader:
                    for key in row:
                        key = key.strip()
                        # Normalize key: remove spaces (consistent with input normalization)
                        key_normalized = key.replace(' ', '')
                        if key_normalized:
                            valid_keys.append(key_normalized)
            except Exception as e:
                log_error(f"CSV reader failed: {e}")
            
            # Method 2: Also try simple line-by-line parsing (in case CSV format is different)
            if not valid_keys:
                for line in response_text.splitlines():
                    line = line.strip()
                    if line:
                        # Remove CSV quotes if present
                        if line.startswith('"') and line.endswith('"'):
                            line = line[1:-1]
                        # Handle escaped quotes
                        line = line.replace('""', '"')
                        # Normalize: remove spaces
                        key_normalized = line.replace(' ', '')
                        if key_normalized:
                            valid_keys.append(key_normalized)
            
            # Remove any spaces from input key (in case user accidentally added spaces)
            normalized_input = _key.strip().replace(' ', '')
            
            # Debug logging
            _logging.debug(f"Looking for key: {normalized_input}")
            _logging.debug(f"Found {len(valid_keys)} keys in CSV")
            if len(valid_keys) <= 10:  # Only log if reasonable number
                _logging.debug(f"Valid keys: {valid_keys}")

            # Try exact match first
            if normalized_input not in valid_keys:
                # Try case-insensitive match (in case there's a case mismatch)
                normalized_lower = normalized_input.lower()
                matched_key = None
                for key in valid_keys:
                    if key.lower() == normalized_lower:
                        matched_key = key
                        break
                
                if matched_key:
                    # Use the matched key (preserve original case from CSV)
                    normalized_input = matched_key
                else:
                    _messagebox.showerror(_("msg.error"), _("activation.invalid_key"))
                    return

            # Remove the key from keys.csv (use normalized key)
            valid_keys.remove(normalized_input)
            self._update_keys_csv(valid_keys)

            _hwid = self._generate_hwid()
            self._append_hwid(_hwid)

            # Notify the user and close the activation window
            _messagebox.showinfo(_("msg.success"), _("activation.success_msg"))
            self._send_discord_notification(_key)
            self._w1.destroy()
            self._p1.destroy()

        except Exception as e:
            log_error(e)
            _messagebox.showerror(_("msg.error"), _f("activation.validate_failed", error=str(e)))

    def _update_keys_csv(self, valid_keys):
        """Update the keys.csv file by removing the used key"""
        _keys_file_url = "https://api.github.com/repos/FrostyHostMC/AutoBE/contents/keys.csv"
        _headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Content-Type": "application/json"
        }
        # Recreate the keys.csv content using proper CSV formatting
        output = io.StringIO()
        csv_writer = csv.writer(output)
        # Write each key as a separate row (properly handles special characters)
        for key in valid_keys:
            csv_writer.writerow([key])
        new_content = output.getvalue().encode('utf-8')
        
        # Base64 encode the content
        encoded_content = base64.b64encode(new_content).decode('utf-8')
        
        try:
            # Get the SHA of the current file
            response = _requests.get(_keys_file_url, headers=_headers)
            response.raise_for_status()
            sha = response.json()['sha']

            # Update the file on GitHub with the new content
            update_data = {
                "message": "Remove used activation key",
                "content": encoded_content,
                "sha": sha
            }
            response = _requests.put(_keys_file_url, json=update_data, headers=_headers)
            response.raise_for_status()
        except Exception as e:
            log_error(e)
            raise Exception(f"Failed to update keys.csv: {str(e)}")

    def _append_hwid(self, _hwid):
        _hwid_file_url = "https://api.github.com/repos/FrostyHostMC/AutoBE/contents/hwid_address.txt"
        _headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Content-Type": "application/json"
        }
        try:
            response = _requests.get(_hwid_file_url, headers=_headers)
            response.raise_for_status()
            
            file_data = response.json()
            current_content = base64.b64decode(file_data['content']).decode('utf-8').rstrip()
            sha = file_data['sha']

            updated_content = f"{current_content}\n{_hwid}\n"
            encoded_content = base64.b64encode(updated_content.encode('utf-8')).decode('utf-8')
            
            update_data = {
                "message": "Add new HWID",
                "content": encoded_content,
                "sha": sha
            }
            put_response = _requests.put(_hwid_file_url, json=update_data, headers=_headers)
            put_response.raise_for_status()
            
            return put_response.json()

        except _requests.exceptions.RequestException as req_err:
            log_error(req_err)
            raise Exception(f"HTTP request failed: {str(req_err)}")
        except Exception as e:
            log_error(e)
            raise Exception(f"Failed to update hwid_address.txt: {str(e)}")

    def _send_discord_notification(self, _key):
        _hwid = self._generate_hwid()
        _webhook_url = os.environ.get("AUTOBE_KEY_WEBHOOK", "")
        if not _webhook_url:
            return
        _data = {
            "content": f"Activation key used: {_key}\nHWID: {_hwid}"
        }
        _requests.post(_webhook_url, json=_data)

    def _generate_hwid(self):
        """Generate a hardware-based unique identifier."""
        if platform.system() == "Windows":
            # Try PowerShell Get-CimInstance (modern replacement for WMIC)
            try:
                ps_command = "Get-CimInstance -ClassName Win32_ComputerSystemProduct | Select-Object -ExpandProperty UUID"
                output = subprocess.check_output(
                    ["powershell", "-Command", ps_command],
                    stderr=subprocess.STDOUT,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
                ).strip()
                if output:
                    return output
            except Exception:
                pass
            # Try WMIC (legacy, may not work on newer Windows)
            try:
                output = subprocess.check_output(
                    ["wmic", "csproduct", "get", "uuid"],
                    stderr=subprocess.STDOUT,
                    text=True
                ).splitlines()
                uuid_value = next(
                    (line.strip() for line in output if line.strip() and line.strip().lower() != "uuid"),
                    None
                )
                if uuid_value:
                    return uuid_value
            except Exception:
                pass
            # Fallback if both methods fail
            return hashlib.md5(platform.node().encode()).hexdigest()
        elif platform.system() == "Linux":
            try:
                with open("/etc/machine-id", "r") as f:
                    return f.read().strip()
            except Exception as e:
                # Fallback if file read fails
                return hashlib.md5(platform.node().encode()).hexdigest()
        elif platform.system() == "Darwin":
            try:
                command = "system_profiler SPHardwareDataType | grep 'Hardware UUID'"
                uuid = subprocess.check_output(command, shell=True).decode().split(": ")[1].strip()
                return uuid
            except Exception as e:
                # Fallback if shell command fails
                return hashlib.md5(platform.node().encode()).hexdigest()
        else:
            return hashlib.md5(platform.node().encode()).hexdigest()
