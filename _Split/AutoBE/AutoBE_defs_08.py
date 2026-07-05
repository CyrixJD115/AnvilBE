class AutoBEApp:

    def organize_and_export(self, selected_files, mode):
        output_lines = []
        total_size = 0

        if mode == "merged":
            output_lines.append("--- MERGE THESE ADDONS IF MERGE SELECTED ---\n\n")
        else:
            output_lines.append("--- ADD THESE ALONE ONLY ---\n\n")

        output_lines.append(f"{'ADDON NAME'.ljust(40)}| {'DATE ADDED'.ljust(15)}| TYPE   | SIZE\n")
        output_lines.append("-" * 80 + "\n")

        for file in selected_files:
            file_name = _os.path.basename(file)
            cleaned_name = self.clean_file_name(file_name)
            date_added = self.get_file_creation_date(file)
            pack_type, size = self.get_pack_type_and_size(file)

            total_size += float(size.split()[0])
            output_lines.append(f"{cleaned_name.ljust(40)}| {date_added.ljust(15)}| {pack_type.ljust(8)}| {size}\n")

        output_lines.append("-" * 80 + "\n")
        output_lines.append(f"FILE SIZE TOTAL: {total_size:.2f} MB\n")

        output_file = _filedialog.asksaveasfilename(
            title=_("filedialog.save_output"),
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt")]
        )

        if output_file:
            write_text_file_utf8(output_file, ''.join(output_lines))
            # Check for suspicious characters
            content = read_text_file_utf8_strip_bom(output_file)
            if '' in content or 'Â§' in content or 'Ã§' in content:
                with open(_LOG_PATH, "a", encoding="utf-8") as log_f:
                    log_f.write(f"Warning: Suspicious character found in {output_file}\n")
            _messagebox.showinfo(_("export.success_title"), _f("export.success_msg", path=output_file))
            self.reset_list_maker()

    def reset_list_maker(self):
        self.selected_files = []
        self.update_file_list()
        self.mode_var.set("merged")
        self.mode_label.config(text=_f("list_maker.mode", mode=_("list_maker.merged")))

    def get_file_creation_date(self, file_path):
        try:
            creation_time = _os.path.getctime(file_path)
            return _datetime.datetime.fromtimestamp(creation_time).strftime("%m/%d/%Y")
        except Exception:
            return "Unknown Date"

    def get_pack_type_and_size(self, file_path):
        try:
            manifest_data = self._get_manifest_data(file_path)
            if manifest_data and 'modules' in manifest_data and len(manifest_data['modules']) > 0:
                pack_type = "Resource" if manifest_data["modules"][0]["type"] == "resources" else "Behavior"
                file_size = _os.path.getsize(file_path) / (1024 * 1024)
                return pack_type, f"{file_size:.2f} MB"
            return "Unknown", "0.00 MB"
        except Exception:
            return "Unknown", "0.00 MB"
    
    def _detect_pack_type(self, file_path):
        """Detect if a .mcpack/.mcaddon file is a Behavior Pack (BP), Resource Pack (RP), or both.
        Returns: 'BP', 'RP', 'BP+RP', or 'Unknown'"""
        try:
            with _zipfile.ZipFile(file_path, 'r') as zip_file:
                # Find manifest.json in the zip
                manifest_path = None
                for filename in zip_file.namelist():
                    # Look for manifest.json at root level (not in subdirectories)
                    if filename.lower() == "manifest.json" or filename.lower().endswith("/manifest.json"):
                        # Prefer root level manifest
                        if filename.lower() == "manifest.json":
                            manifest_path = filename
                            break
                        elif manifest_path is None:
                            manifest_path = filename
                
                if manifest_path:
                    # Use the improved _get_manifest_data method which handles comments properly
                    manifest = self._get_manifest_data(file_path)
                    if manifest:
                        modules = manifest.get("modules", [])
                        
                        has_behavior = False
                        has_resource = False
                        
                        for module in modules:
                            module_type = module.get("type", "").lower()
                            if module_type in ("data", "script"):
                                has_behavior = True
                            elif module_type == "resources":
                                has_resource = True
                        
                        if has_behavior and has_resource:
                            return "BP+RP"
                        elif has_behavior:
                            return "BP"
                        elif has_resource:
                            return "RP"
                        else:
                            return "Unknown"
            return "Unknown"
        except Exception as e:
            return "Unknown"

    @staticmethod
    def _version_to_group_key(ver):
        """Convert an exact @minecraft/server version string to a broad grouping key.

        Groups by major version + stability so minor-version differences within the same
        major are merged together (they are backwards-compatible inside Bedrock):
            '1.5.0'      -> '1_x'
            '1.19.0'     -> '1_x'   (same group as 1.5.0)
            '2.0.0'      -> '2_x'
            '2.6.0'      -> '2_x'   (same group as 2.0.0)
            '2.5.0-beta' -> '2_x_beta'
            '2.7.0-beta' -> '2_x_beta'  (same group)
            '3.0.0-alpha'-> '3_x_alpha'
        """
        if not ver:
            return "none"
        v = str(ver).strip().lower()
        is_alpha   = 'alpha'   in v
        is_beta    = not is_alpha and any(s in v for s in ('beta', 'preview', 'rc'))
        m = _re.match(r'^(\d+)', v)
        if not m:
            return "none"
        major = m.group(1)
        if is_alpha:
            return f"{major}_x_alpha"
        elif is_beta:
            return f"{major}_x_beta"
        else:
            return f"{major}_x"

    def _group_files_by_script_api_version(self, file_list):
        """Group .mcpack/.mcaddon file paths by script API version bucket.
        Returns dict: folder_key (e.g. '1_x', '2_x', '2_x_beta', 'none') -> list of paths.

        Packs within the same major version are merged together — minor versions are
        backwards-compatible inside Bedrock (it promotes them automatically).

        Two-pass strategy so paired BP/RP halves always land in the same group:
          Pass 1 — assign every pack to its major-version bucket (BP packs get a real
                   version key; RP-only packs tentatively go to 'none').
          Pass 2 — for each RP pack in 'none', look for a BP pack with the same base name
                   in a versioned group; if found, move the RP into that same group so the
                   behavior and resource halves of the addon end up in one merged output.
        """
        # Pass 1: classify every file
        file_group = {}   # file_path -> folder_key
        rp_files = []     # RP-only packs (tentatively 'none')

        for file_path in file_list:
            folder_key = "none"
            try:
                manifest = self._get_manifest_data(file_path)
                if not manifest:
                    file_group[file_path] = folder_key
                    continue
                modules = manifest.get("modules") or []
                is_rp_only = (
                    isinstance(modules, list) and len(modules) > 0 and
                    isinstance(modules[0], dict) and
                    modules[0].get("type") == "resources"
                )
                if is_rp_only:
                    file_group[file_path] = "none"
                    rp_files.append(file_path)
                    continue
                ver = self._get_pack_script_api_version(manifest)
                if ver:
                    folder_key = self._version_to_group_key(ver)
                file_group[file_path] = folder_key
            except Exception:
                file_group[file_path] = folder_key

        # Pass 2: pair each RP file with its BP counterpart (if any)
        # Build a map: base_name -> version_key for all BP files in a versioned group
        bp_base_to_version = {}
        for fp, vk in file_group.items():
            if vk != "none" and fp not in rp_files:
                base = IdentifierManager._pack_base_name(fp)
                bp_base_to_version[base] = vk

        for rp_path in rp_files:
            base = IdentifierManager._pack_base_name(rp_path)
            matched_ver = bp_base_to_version.get(base)
            if matched_ver:
                file_group[rp_path] = matched_ver

        # Build final groups dict
        groups = defaultdict(list)
        for fp, vk in file_group.items():
            groups[vk].append(fp)
        return dict(groups)

    def _get_pack_display_info(self, file_path):
        """Get pack display name (from manifest header) and pack_icon as a Tk PhotoImage thumbnail.
        Returns (display_name, photo_image_or_None). Uses filename + pack type if manifest unavailable."""
        default_name = _os.path.basename(file_path)
        pack_type = self._detect_pack_type(file_path)
        if pack_type != "Unknown":
            default_display = f"{default_name} [{pack_type}]"
        else:
            default_display = default_name
        display_name = default_display
        photo = None
        full_photo = None
        pack_name = None
        try:
            manifest = self._get_manifest_data(file_path)
            if manifest:
                header = manifest.get("header") or {}
                name_val = header.get("name")
                if isinstance(name_val, str):
                    pack_name = name_val.strip() or default_name
                elif isinstance(name_val, dict):
                    pack_name = name_val.get("text") or name_val.get("translate") or default_name
                    if isinstance(pack_name, dict):
                        pack_name = (list(pack_name.values()) or [default_name])[0]
                    pack_name = str(pack_name).strip() if pack_name else default_name
                else:
                    pack_name = default_name
            else:
                pack_name = default_name

            # Resolve localization key names like "pack.name" from texts/en_US.(lang|json)
            resolved_name = None
            try:
                key = str(pack_name).strip() if pack_name else ''
                if key and key != default_name and (' ' not in key):
                    with _zipfile.ZipFile(file_path, 'r') as _zf:
                        candidates = [
                            'texts/en_US.lang',
                            'texts/en_US.json',
                            'R/texts/en_US.lang',
                            'R/texts/en_US.json',
                            'B/texts/en_US.lang',
                            'B/texts/en_US.json',
                        ]
                        for path in candidates:
                            try:
                                raw = _zf.read(path)
                            except KeyError:
                                continue
                            try:
                                text = raw.decode('utf-8')
                            except Exception:
                                text = raw.decode('latin-1', errors='ignore')
                            if path.endswith('.lang'):
                                m = _parse_lang_kv(text)
                                if key in m:
                                    resolved_name = m.get(key)
                                    break
                            else:
                                try:
                                    data = _json.loads(text)
                                except Exception:
                                    data = None
                                if isinstance(data, dict) and key in data:
                                    resolved_name = str(data.get(key))
                                    break
                if resolved_name:
                    pack_name = resolved_name.strip() or pack_name
            except Exception:
                pass

            display_name = f"{pack_name} [{pack_type}]" if pack_type != "Unknown" else pack_name
        except Exception:
            display_name = default_display
            pack_name = default_name
        try:
            with _zipfile.ZipFile(file_path, 'r') as zf:
                # Prefer icon from same directory as manifest (root, then behavior_pack, then first subdir)
                manifest_path = None
                root_m, bp_m, first_m = None, None, None
                for name in zf.namelist():
                    name_norm = name.replace('\\', '/')
                    name_lower = name_norm.lower()
                    if name_lower == 'manifest.json':
                        root_m = name_norm
                        break
                    if name_lower.endswith('/manifest.json'):
                        if first_m is None:
                            first_m = name_norm
                        if 'behavior_pack' in name_lower:
                            bp_m = name_norm
                if root_m:
                    manifest_path = root_m
                elif bp_m:
                    manifest_path = bp_m
                elif first_m:
                    manifest_path = first_m
                manifest_dir = (_os.path.dirname(manifest_path) + '/') if manifest_path else ''
                icon_name = None
                icon_in_manifest_dir = None
                manifest_dir_lower = manifest_dir.lower() if manifest_dir else ''
                for n in zf.namelist():
                    n_norm = n.replace('\\', '/')
                    n_lower = n_norm.lower()
                    if not (n_lower.endswith('pack_icon.png') or n_lower.endswith('pack_icon.jpg') or n_lower.endswith('pack_icon.jpeg')):
                        continue
                    if manifest_dir_lower and n_lower.startswith(manifest_dir_lower):
                        icon_in_manifest_dir = n_norm
                        break
                    if icon_name is None:
                        icon_name = n_norm
                if icon_in_manifest_dir:
                    icon_name = icon_in_manifest_dir
                if icon_name:
                    data = zf.read(icon_name)
                    # Prefer PIL/Pillow: Tk's PhotoImage often fails on some PNGs on Windows
                    if _PIL_AVAILABLE and data:
                        try:
                            img = _PIL_Image.open(io.BytesIO(data))
                            # Handle RGBA/P: composite onto white so transparency doesn't become black
                            if img.mode in ('RGBA', 'LA', 'P'):
                                if img.mode == 'P' and 'transparency' in img.info:
                                    img = img.convert('RGBA')
                                bg = _PIL_Image.new('RGB', img.size, (255, 255, 255))
                                if img.mode in ('RGBA', 'LA'):
                                    bg.paste(img, mask=img.split()[-1])
                                else:
                                    bg.paste(img)
                                img = bg
                            elif img.mode not in ('RGB', 'L'):
                                img = img.convert('RGB')
                            if img.mode == 'L':
                                img = img.convert('RGB')
                            thumb_resample = getattr(_PIL_Image.Resampling, 'LANCZOS', None) or getattr(_PIL_Image, 'LANCZOS', 1)
                            img.thumbnail((48, 48), thumb_resample)
                            photo = _PIL_ImageTk.PhotoImage(img)
                            return (display_name, photo, None)
                        except Exception:
                            # PIL decoded OK but PhotoImage failed; re-encode to simple PNG and try Tk from file
                            try:
                                img = _PIL_Image.open(io.BytesIO(data))
                                if img.mode in ('RGBA', 'LA', 'P'):
                                    if img.mode == 'P' and 'transparency' in img.info:
                                        img = img.convert('RGBA')
                                    bg = _PIL_Image.new('RGB', img.size, (255, 255, 255))
                                    if img.mode in ('RGBA', 'LA'):
                                        bg.paste(img, mask=img.split()[-1])
                                    else:
                                        bg.paste(img)
                                    img = bg
                                elif img.mode not in ('RGB', 'L'):
                                    img = img.convert('RGB')
                                if img.mode == 'L':
                                    img = img.convert('RGB')
                                img.thumbnail((48, 48), getattr(_PIL_Image.Resampling, 'LANCZOS', 1) or 1)
                                fd, tmp = _tempfile.mkstemp(suffix='.png')
                                _os.close(fd)
                                img.save(tmp, 'PNG')
                                full_photo = _tk.PhotoImage(file=tmp)
                                scale = max(1, min(full_photo.width(), full_photo.height()) // 48)
                                photo = full_photo.subsample(scale, scale)
                                try:
                                    _os.unlink(tmp)
                                except Exception:
                                    pass
                                return (display_name, photo, full_photo)
                            except Exception:
                                pass
                    # Fallback: Tk PhotoImage from temp file
                    ext = '.png' if icon_name.lower().endswith('.png') else '.jpg'
                    fd, tmp = _tempfile.mkstemp(suffix=ext)
                    try:
                        _os.write(fd, data)
                        _os.close(fd)
                        full_photo = _tk.PhotoImage(file=tmp)
                        w, h = full_photo.width(), full_photo.height()
                        scale = max(1, min(w, h) // 48)
                        photo = full_photo.subsample(scale, scale)
                        return (display_name, photo, full_photo)
                    except Exception:
                        pass
                    finally:
                        try:
                            _os.unlink(tmp)
                        except Exception:
                            pass
        except Exception:
            pass
        return (display_name, None, None)

    def init_help_tab(self):
        # Main container with split layout (navigation + content)
        main_container = _tk.Frame(self.help_frame, bg='#000000')
        main_container.pack(fill='both', expand=True, padx=15, pady=15)
        
        # Left navigation panel; width responds to window size so it fits on small screens
        nav_frame = _tk.Frame(main_container, bg='#1a1a1a', width=260)
        nav_frame.pack(side='left', fill='y', padx=(0, 15))
        nav_frame.pack_propagate(False)
        def _help_nav_resize(event):
            try:
                w = max(180, min(260, event.width // 3))
                if nav_frame.winfo_exists():
                    nav_frame.configure(width=w)
                    for child in nav_frame.winfo_children():
                        try:
                            if child.winfo_class() == 'Button':
                                child.configure(wraplength=max(120, w - 30))
                        except Exception:
                            pass
            except Exception:
                pass
        main_container.bind('<Configure>', _help_nav_resize)
        
        # Navigation title
        nav_title = _tk.Label(nav_frame, text="📚 " + _("help.nav_topics"), bg='#1a1a1a', fg='#FFFFFF', 
                             font=("Segoe UI", 13, "bold"))
        nav_title.pack(pady=(15, 20))
        
        # Navigation buttons
        self.help_sections = {}
        _help_nav_keys = {"Overview": "help.overview", "Getting Started": "help.getting_started", "What Happens During Merging": "help.merging", "Common Errors": "help.common_errors", "Best Practices": "help.best_practices", "Processing Overview": "help.processing_overview", "Important Notes": "help.important_notes"}
        nav_buttons = [
            ("Overview", "📌"),
            ("Getting Started", "🚀"),
            ("What Happens During Merging", "📦"),
            ("Common Errors", "⚠️"),
            ("Best Practices", "💡"),
            ("Processing Overview", "⚙️"),
            ("Important Notes", "📋"),
            ("Modpack Organization", "📊")
        ]
        
        self.current_help_section = _tk.StringVar(value="Overview")
        
        for section_name, icon in nav_buttons:
            btn = _tk.Button(nav_frame, 
                           text=f"{icon} {_(_help_nav_keys.get(section_name, section_name))}",
                           command=lambda s=section_name: self._show_help_section(s),
                           bg='#0A0A0A', fg='#FFFFFF', font=("Segoe UI", 10),
                           relief='flat', anchor='w', padx=15, pady=12,
                           cursor='hand2', activebackground='#9333ea', activeforeground='#FFFFFF',
                           wraplength=230, justify='left')
            btn.pack(fill='x', padx=10, pady=5)
            self.help_sections[section_name] = btn
        
        # Right content area with scrollable canvas
        content_container = _tk.Frame(main_container, bg='#000000')
        content_container.pack(side='right', fill='both', expand=True)
        
        # Create canvas with hover-scroll only (no visible scrollbar)
        canvas = _tk.Canvas(content_container, bg='#000000', highlightthickness=0)
        self.help_content_frame = _tk.Frame(canvas, bg='#000000')
        
        def update_scroll_region(event=None):
            canvas.update_idletasks()
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        self.help_content_frame.bind("<Configure>", update_scroll_region)
        
        canvas.create_window((0, 0), window=self.help_content_frame, anchor="nw")
        
        # Update canvas width and help text wraplength when resized so content fits the window
        def set_wraplength_recursive(widget, wraplen):
            try:
                if widget.winfo_class() == 'Label':
                    widget.configure(wraplength=max(200, wraplen))
                for child in widget.winfo_children():
                    set_wraplength_recursive(child, wraplen)
            except Exception:
                pass
        def configure_canvas_width(event):
            canvas_width = event.width
            if canvas.find_all():
                canvas.itemconfig(canvas.find_all()[0], width=canvas_width)
            set_wraplength_recursive(self.help_content_frame, canvas_width - 40)
        canvas.bind('<Configure>', configure_canvas_width)
        
        # Pack canvas (no scrollbar shown)
        canvas.pack(side="left", fill="both", expand=True)

        # Hover-based mouse wheel scrolling (active only while cursor is over Help content)
        def _on_mousewheel(event):
            try:
                if canvas.winfo_exists():
                    canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            except Exception:
                pass
        def _help_scroll_bind_enter(event):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
        def _help_scroll_bind_leave(event):
            try:
                canvas.unbind_all("<MouseWheel>")
            except Exception:
                pass
        canvas.bind("<Enter>", _help_scroll_bind_enter)
        canvas.bind("<Leave>", _help_scroll_bind_leave)
        self.help_content_frame.bind("<Enter>", _help_scroll_bind_enter)
        self.help_content_frame.bind("<Leave>", _help_scroll_bind_leave)
        
        # Store canvas reference for scrolling
        self.help_canvas = canvas
        
        # Create all help sections (initially hidden)
        self._create_help_sections()
        
        # Show default section (Overview so users see what the app is and how it works first)
        self._show_help_section("Overview")
    
    def _open_discord_invite(self):
        """Open Discord invite link in default browser."""
        try:
            webbrowser.open("https://discord.gg/M8jDRZW8j4")
        except Exception as e:
            log_error(f"Failed to open Discord invite: {e}")
            _messagebox.showerror(_("msg.error"), _("error.discord_failed"))
    
    def _create_help_sections(self):
        """Create all help section content frames."""
        # Store all section frames
        self.help_section_frames = {}
        
        # Overview Section (what AutoBE is, the three tabs, activation)
        self.help_section_frames["Overview"] = self._create_overview_section()
        
        # Getting Started Section
        self.help_section_frames["Getting Started"] = self._create_getting_started_section()
        
        # What Happens During Merging Section
        self.help_section_frames["What Happens During Merging"] = self._create_merging_section()
        
        # Common Errors Section
        self.help_section_frames["Common Errors"] = self._create_errors_section()
        
        # Best Practices Section
        self.help_section_frames["Best Practices"] = self._create_best_practices_section()
        
        # Processing Overview Section
        self.help_section_frames["Processing Overview"] = self._create_processing_section()
        
        # Important Notes Section
        self.help_section_frames["Important Notes"] = self._create_disclaimer_section()
        
        # Modpack Organization Section
        self.help_section_frames["Modpack Organization"] = self._create_modpack_organization_section()
    
    def _show_help_section(self, section_name):
        """Show the selected help section and hide others."""
        # Hide all sections
        for frame in self.help_section_frames.values():
            frame.pack_forget()
        
        # Show selected section
        if section_name in self.help_section_frames:
            self.help_section_frames[section_name].pack(fill='both', expand=True, padx=0, pady=0)
            self.current_help_section.set(section_name)
            
            # Update button styles
            for name, btn in self.help_sections.items():
                if name == section_name:
                    btn.config(bg='#9333ea', fg='#FFFFFF')
                else:
                    btn.config(bg='#0A0A0A', fg='#FFFFFF')
            
            # Scroll to top and update scroll region
            self.help_canvas.yview_moveto(0)
            self.help_canvas.update_idletasks()
            # Force update of scroll region after showing section
            self._root.after(100, lambda: self.help_canvas.configure(scrollregion=self.help_canvas.bbox("all")))
            # Force update of scroll region after showing section
            self._root.after(100, lambda: self.help_canvas.configure(scrollregion=self.help_canvas.bbox("all")))
    
    def _create_overview_section(self):
        """Create the Overview help section: what AutoBE is, the three tabs, activation."""
        section_frame = _tk.Frame(self.help_content_frame, bg='#000000')
        
        overview_card = _tk.LabelFrame(section_frame, text="📌 " + _("help.overview"), 
                                       bg='#1a1a1a', fg='#FFFFFF', font=("Segoe UI", 14, "bold"),
                                       relief='flat', bd=0)
        overview_card.pack(fill='x', padx=0, pady=(0, 15))
        overview_inner = _tk.Frame(overview_card, bg='#1a1a1a')
        overview_inner.pack(fill='both', expand=True, padx=20, pady=15)
        
        _tk.Label(overview_inner, text=_("help.overview_what_is"), bg='#1a1a1a', fg='#FFFFFF',
                  font=("Segoe UI", 11), justify='left', anchor='w', wraplength=680).pack(fill='x', pady=(0, 15))
        
        _tk.Label(overview_inner, text=_("help.overview_tabs_intro"), bg='#1a1a1a', fg='#9333ea',
                  font=("Segoe UI", 11, "bold"), anchor='w').pack(fill='x', pady=(0, 8))
        _tk.Label(overview_inner, text=_("help.overview_tabs_autobe"), bg='#1a1a1a', fg='#CCCCCC',
                  font=("Segoe UI", 10), justify='left', anchor='w', wraplength=680).pack(fill='x', pady=(0, 6))
        _tk.Label(overview_inner, text=_("help.overview_tabs_mcpacker"), bg='#1a1a1a', fg='#CCCCCC',
                  font=("Segoe UI", 10), justify='left', anchor='w', wraplength=680).pack(fill='x', pady=(0, 6))
        _tk.Label(overview_inner, text=_("help.overview_tabs_list_maker"), bg='#1a1a1a', fg='#CCCCCC',
                  font=("Segoe UI", 10), justify='left', anchor='w', wraplength=680).pack(fill='x', pady=(0, 15))
        
        _tk.Label(overview_inner, text=_("help.overview_activation_intro"), bg='#1a1a1a', fg='#9333ea',
                  font=("Segoe UI", 11, "bold"), anchor='w').pack(fill='x', pady=(0, 8))
        _tk.Label(overview_inner, text=_("help.overview_activation"), bg='#1a1a1a', fg='#CCCCCC',
                  font=("Segoe UI", 10), justify='left', anchor='w', wraplength=680).pack(fill='x', pady=(0, 5))
        
        return section_frame
    
    def _create_getting_started_section(self):
        """Create the Getting Started help section."""
        section_frame = _tk.Frame(self.help_content_frame, bg='#000000')
        
        # Welcome Section
        welcome_card = _tk.LabelFrame(section_frame, text="📖 " + _("help.welcome"), 
                                     bg='#1a1a1a', fg='#FFFFFF', font=("Segoe UI", 14, "bold"),
                                     relief='flat', bd=0)
        welcome_card.pack(fill='x', padx=0, pady=(0, 15))
        
        welcome_inner = _tk.Frame(welcome_card, bg='#1a1a1a')
        welcome_inner.pack(fill='both', expand=True, padx=20, pady=15)
        
        welcome_text = _tk.Label(welcome_inner, 
                                 text=_("help.welcome_text"),
                                 bg='#1a1a1a', fg='#FFFFFF', font=("Segoe UI", 11),
                                 justify='left', anchor='w')
        welcome_text.pack(fill='x', pady=(0, 5))
        
        # Discord invite section
        discord_frame = _tk.Frame(welcome_inner, bg='#1a1a1a')
        discord_frame.pack(fill='x', pady=(10, 0))
        
        discord_label = _tk.Label(discord_frame,
                                 text=_("help.need_help_discord"),
                                 bg='#1a1a1a', fg='#FFFFFF', font=("Segoe UI", 10),
                                 justify='left', anchor='w')
        discord_label.pack(side='left', padx=(0, 10))
        
        discord_btn = _tk.Button(discord_frame,
                               text="💬 " + _("help.join_discord"),
                               command=lambda: self._open_discord_invite(),
                               bg='#5865F2', fg='#FFFFFF', font=("Segoe UI", 10, "bold"),
                               relief='flat', padx=15, pady=8,
                               cursor='hand2', activebackground='#4752C4', activeforeground='#FFFFFF')
        discord_btn.pack(side='left')
        
        # Complete Usage Guide Section
        usage_card = _tk.LabelFrame(section_frame, text="📚 " + _("help.usage_guide"), 
                                    bg='#1a1a1a', fg='#FFFFFF', font=("Segoe UI", 14, "bold"),
                                    relief='flat', bd=0)
        usage_card.pack(fill='both', expand=True, padx=0, pady=(0, 15))
        
        usage_inner = _tk.Frame(usage_card, bg='#1a1a1a')
        usage_inner.pack(fill='both', expand=True, padx=20, pady=15)
        
        usage_steps = [
            (_("help.usage1_title"), _("help.usage1_desc")),
            (_("help.usage2_title"), _("help.usage2_desc")),
            (_("help.usage3_title"), _("help.usage3_desc")),
            (_("help.usage4_title"), _("help.usage4_desc")),
            (_("help.usage5_title"), _("help.usage5_desc")),
        ]
        
        for i, (title, description) in enumerate(usage_steps, 1):
            step_frame = _tk.Frame(usage_inner, bg='#0A0A0A', relief='flat')
            step_frame.pack(fill='x', pady=(0, 10), padx=5)
            
            step_title = _tk.Label(step_frame, text=f"{i}. {title}", bg='#0A0A0A', fg='#9333ea',
                                   font=("Segoe UI", 11, "bold"), anchor='w')
            step_title.pack(fill='x', padx=12, pady=(10, 5))
            
            step_desc = _tk.Label(step_frame, text=description, bg='#0A0A0A', fg='#CCCCCC',
                                 font=("Segoe UI", 10), anchor='w', justify='left', wraplength=680)
            step_desc.pack(fill='x', padx=12, pady=(0, 10))

        # Music setup guide (background music + playlists + controls)
        music_card = _tk.LabelFrame(section_frame, text="🎵 Music Setup", 
                                    bg='#1a1a1a', fg='#FFFFFF', font=("Segoe UI", 14, "bold"),
                                    relief='flat', bd=0)
        music_card.pack(fill='x', padx=0, pady=(0, 15))
        music_inner = _tk.Frame(music_card, bg='#1a1a1a')
        music_inner.pack(fill='both', expand=True, padx=20, pady=15)

        _tk.Label(
            music_inner,
            text="How to set up music and playlists:",
            bg='#1a1a1a',
            fg='#9333ea',
            font=("Segoe UI", 11, "bold"),
            anchor='w'
        ).pack(fill='x', pady=(0, 8))

        music_steps = [
            "1) Put audio files in the app's music folder (supported: .mp3, .ogg, .wav).",
            "2) Optional playlists: create folders inside music (for example: music\\lofi, music\\hype).",
            "3) Open Settings -> Background music and enable 'Play background music'.",
            "4) Choose a Playlist (All music or a folder name), then set volume/shuffle.",
            "5) Use ⏮ and ⏭ in Settings to go previous/next instantly.",
            "6) The 'Now Playing' popup appears on each new track; long names scroll automatically.",
        ]
        for line in music_steps:
            _tk.Label(
                music_inner,
                text=line,
                bg='#1a1a1a',
                fg='#CCCCCC',
                font=("Segoe UI", 10),
                anchor='w',
                justify='left',
                wraplength=680
            ).pack(fill='x', pady=(0, 4))

        _tk.Label(
            music_inner,
            text="Tip: Name your default main track background.mp3 (or background.ogg/.wav) to make it the preferred first song.",
            bg='#1a1a1a',
            fg='#9ca3af',
            font=("Segoe UI", 9),
            anchor='w',
            justify='left',
            wraplength=680
        ).pack(fill='x', pady=(8, 0))
        
        return section_frame
    
    def _create_merging_section(self):
        """Create the Merging Process section."""
        section_frame = _tk.Frame(self.help_content_frame, bg='#000000')
        
        merging_card = _tk.LabelFrame(section_frame, text="📦 " + _("help.merging"), 
                                     bg='#1a1a1a', fg='#FFFFFF', font=("Segoe UI", 14, "bold"),
                                     relief='flat', bd=0)
        merging_card.pack(fill='both', expand=True, padx=0, pady=(0, 15))
        
        merging_inner = _tk.Frame(merging_card, bg='#1a1a1a')
        merging_inner.pack(fill='both', expand=True, padx=20, pady=15)
        
        merging_info = [
            (_("help.merge1_title"), _("help.merge1_desc")),
            (_("help.merge2_title"), _("help.merge2_desc")),
            (_("help.merge3_title"), _("help.merge3_desc")),
        ]
        
        for title, description in merging_info:
            info_frame = _tk.Frame(merging_inner, bg='#0A0A0A', relief='flat')
            info_frame.pack(fill='x', pady=(0, 12), padx=5)
            
            info_title = _tk.Label(info_frame, text=f"• {title}", bg='#0A0A0A', fg='#9333ea',
                                  font=("Segoe UI", 11, "bold"), anchor='w', wraplength=650)
            info_title.pack(fill='x', padx=12, pady=(12, 6))
            
            info_desc = _tk.Label(info_frame, text=description, bg='#0A0A0A', fg='#CCCCCC',
                                 font=("Segoe UI", 10), anchor='w', justify='left', wraplength=650)
            info_desc.pack(fill='x', padx=12, pady=(0, 12))

        # Practical merge workflow users can follow step-by-step
        workflow_card = _tk.Frame(merging_inner, bg='#0A0A0A', relief='flat')
        workflow_card.pack(fill='x', pady=(0, 12), padx=5)
        _tk.Label(workflow_card, text="• Complete merge workflow (recommended order)", bg='#0A0A0A', fg='#9333ea',
                  font=("Segoe UI", 11, "bold"), anchor='w', wraplength=650).pack(fill='x', padx=12, pady=(12, 6))
        workflow_steps = [
            "1) Add only valid .mcpack files in the AutoBE tab (remove duplicates before running).",
            "2) Set output folder to a clean location (empty/new folder is best).",
            "3) Choose whether to merge by script version in Settings if your packs mix API versions.",
            "4) Start process and wait for all 4 progress steps to complete.",
            "5) Optional after merge: use linked packs list, remove one addon, and re-merge automatically.",
            "6) Optional after merge: customize pack name/description/icon/author for final release.",
        ]
        for line in workflow_steps:
            _tk.Label(workflow_card, text=line, bg='#0A0A0A', fg='#CCCCCC', font=("Segoe UI", 10),
                      anchor='w', justify='left', wraplength=650).pack(fill='x', padx=12, pady=(0, 4))
        _tk.Label(workflow_card, text="Tip: keep original source packs unchanged; treat merged output as a build artifact.",
                  bg='#0A0A0A', fg='#9ca3af', font=("Segoe UI", 9), anchor='w', justify='left', wraplength=650).pack(fill='x', padx=12, pady=(8, 12))

        # Linked packs/remove flow documentation
        linked_card = _tk.Frame(merging_inner, bg='#0A0A0A', relief='flat')
        linked_card.pack(fill='x', pady=(0, 12), padx=5)
        _tk.Label(linked_card, text="• Linked packs: remove one addon from a merge", bg='#0A0A0A', fg='#9333ea',
                  font=("Segoe UI", 11, "bold"), anchor='w', wraplength=650).pack(fill='x', padx=12, pady=(12, 6))
        linked_steps = [
            "1) Run a merge at least once so _autobe_merge_manifest.json is created in output.",
            "2) Open linked packs (auto popup if enabled in Settings, or from linked packs flow).",
            "3) Click Remove on the addon you want to exclude.",
            "4) AutoBE re-runs the merge using remaining source packs and overwrites output.",
            "5) If source files moved/deleted, re-add valid packs and merge again.",
        ]
        for line in linked_steps:
            _tk.Label(linked_card, text=line, bg='#0A0A0A', fg='#CCCCCC', font=("Segoe UI", 10),
                      anchor='w', justify='left', wraplength=650).pack(fill='x', padx=12, pady=(0, 4))
        _tk.Label(linked_card, text="Important: at least one pack must remain; removing the last pack is blocked.",
                  bg='#0A0A0A', fg='#fca5a5', font=("Segoe UI", 9), anchor='w', justify='left', wraplength=650).pack(fill='x', padx=12, pady=(8, 12))

        # Script / API version behavior explanation
        script_card = _tk.Frame(merging_inner, bg='#0A0A0A', relief='flat')
        script_card.pack(fill='x', pady=(0, 4), padx=5)
        _tk.Label(script_card, text="• Script/API version handling", bg='#0A0A0A', fg='#9333ea',
                  font=("Segoe UI", 11, "bold"), anchor='w', wraplength=650).pack(fill='x', padx=12, pady=(12, 6))
        _tk.Label(script_card,
                  text="When packs use different @minecraft/server API versions, enable 'merge by script version' in Settings. AutoBE creates separate subfolders per version, reducing script conflicts and runtime breakage.",
                  bg='#0A0A0A', fg='#CCCCCC', font=("Segoe UI", 10), anchor='w', justify='left', wraplength=650).pack(fill='x', padx=12, pady=(0, 12))
        
        return section_frame
    
    def _create_errors_section(self):
        """Create the Common Errors section."""
        section_frame = _tk.Frame(self.help_content_frame, bg='#000000')
        
        errors_card = _tk.LabelFrame(section_frame, text="⚠️ " + _("help.common_errors_full"), 
                                    bg='#1a1a1a', fg='#FFFFFF', font=("Segoe UI", 14, "bold"),
                                    relief='flat', bd=0)
        errors_card.pack(fill='both', expand=True, padx=0, pady=(0, 15))
        
        errors_inner = _tk.Frame(errors_card, bg='#1a1a1a')
        errors_inner.pack(fill='both', expand=True, padx=20, pady=15)
        
        error_solutions = [
            (_("help.error1_title"), _("help.error1_desc")),
            (_("help.error2_title"), _("help.error2_desc")),
            (_("help.error3_title"), _("help.error3_desc")),
            (_("help.error4_title"), _("help.error4_desc")),
            (_("help.error5_title"), _("help.error5_desc")),
        ]
        
        for title, description in error_solutions:
            error_frame = _tk.Frame(errors_inner, bg='#0A0A0A', relief='flat')
            error_frame.pack(fill='x', pady=(0, 12), padx=5)
            
            error_title = _tk.Label(error_frame, text=title, bg='#0A0A0A', fg='#FF6B6B',
                                   font=("Segoe UI", 11, "bold"), anchor='w', wraplength=650)
            error_title.pack(fill='x', padx=12, pady=(12, 6))
            
            error_desc = _tk.Label(error_frame, text=description, bg='#0A0A0A', fg='#CCCCCC',
                                  font=("Segoe UI", 10), anchor='w', justify='left', wraplength=650)
            error_desc.pack(fill='x', padx=12, pady=(0, 12))

        # Troubleshooting matrix for real modpack merge failures
        quickfix_card = _tk.Frame(errors_inner, bg='#0A0A0A', relief='flat')
        quickfix_card.pack(fill='x', pady=(0, 12), padx=5)
        _tk.Label(quickfix_card, text="Quick fixes by symptom", bg='#0A0A0A', fg='#FF6B6B',
                  font=("Segoe UI", 11, "bold"), anchor='w', wraplength=650).pack(fill='x', padx=12, pady=(12, 8))
        quick_fixes = [
            "• 'No manifest.json' -> verify pack is a valid .mcpack/.mcaddon and not a random zip export.",
            "• Merge finishes but game crashes -> enable merge-by-script-version and test each output folder separately.",
            "• Textures/models missing -> check pack order and duplicate file collisions; retry with fewer packs to isolate.",
            "• Linked packs remove fails -> ensure source files still exist at original paths from merge manifest.",
            "• Update errors on Windows -> run app as admin and ensure antivirus did not quarantine the new exe.",
            "• Music not playing -> check Settings toggle, playlist selection, and supported audio file extensions.",
        ]
        for line in quick_fixes:
            _tk.Label(quickfix_card, text=line, bg='#0A0A0A', fg='#CCCCCC', font=("Segoe UI", 10),
                      anchor='w', justify='left', wraplength=650).pack(fill='x', padx=12, pady=(0, 4))
        _tk.Label(quickfix_card, text="Debug workflow: remove half the packs, re-merge, then binary-search the failing addon.",
                  bg='#0A0A0A', fg='#9ca3af', font=("Segoe UI", 9), anchor='w', justify='left', wraplength=650).pack(fill='x', padx=12, pady=(8, 12))
        
        return section_frame
    
    def _create_best_practices_section(self):
        """Create the Best Practices section."""
        section_frame = _tk.Frame(self.help_content_frame, bg='#000000')
        
        best_practices_card = _tk.LabelFrame(section_frame, text="💡 " + _("help.best_practices"), 
                                            bg='#1a1a1a', fg='#FFFFFF', font=("Segoe UI", 14, "bold"),
                                            relief='flat', bd=0)
        best_practices_card.pack(fill='both', expand=True, padx=0, pady=(0, 15))
        
        best_practices_inner = _tk.Frame(best_practices_card, bg='#1a1a1a')
        best_practices_inner.pack(fill='both', expand=True, padx=20, pady=15)
        
        practices = [
            _("help.practice1"), _("help.practice2"), _("help.practice3"), _("help.practice4"),
            _("help.practice5"), _("help.practice6"),
        ]
        
        for practice in practices:
            practice_label = _tk.Label(best_practices_inner, text=f"✓ {practice}", bg='#1a1a1a', fg='#CCCCCC',
                                      font=("Segoe UI", 10), anchor='w', justify='left', wraplength=650)
            practice_label.pack(fill='x', pady=(0, 8))
        
        return section_frame
    
    def _create_processing_section(self):
        """Create the Processing Overview section."""
        section_frame = _tk.Frame(self.help_content_frame, bg='#000000')
        
        processing_card = _tk.LabelFrame(section_frame, text="⚙️ " + _("help.processing_overview"), 
                                       bg='#1a1a1a', fg='#FFFFFF', font=("Segoe UI", 14, "bold"),
                                       relief='flat', bd=0)
        processing_card.pack(fill='both', expand=True, padx=0, pady=(0, 15))
        
        processing_inner = _tk.Frame(processing_card, bg='#1a1a1a')
        processing_inner.pack(fill='both', expand=True, padx=20, pady=15)
        
        processing_steps = [
            (_("help.proc1_title"), _("help.proc1_desc")),
            (_("help.proc2_title"), _("help.proc2_desc")),
            (_("help.proc3_title"), _("help.proc3_desc")),
            (_("help.proc4_title"), _("help.proc4_desc")),
        ]
        
        for title, description in processing_steps:
            step_frame = _tk.Frame(processing_inner, bg='#0A0A0A', relief='flat')
            step_frame.pack(fill='x', pady=(0, 10), padx=5)
            
            step_title = _tk.Label(step_frame, text=f"• {title}", bg='#0A0A0A', fg='#9333ea',
                                  font=("Segoe UI", 11, "bold"), anchor='w')
            step_title.pack(fill='x', padx=12, pady=(10, 5))
            
            step_desc = _tk.Label(step_frame, text=description, bg='#0A0A0A', fg='#CCCCCC',
                                 font=("Segoe UI", 10), anchor='w', justify='left', wraplength=680)
            step_desc.pack(fill='x', padx=12, pady=(0, 10))

        internals_card = _tk.Frame(processing_inner, bg='#0A0A0A', relief='flat')
        internals_card.pack(fill='x', pady=(0, 4), padx=5)
        _tk.Label(internals_card, text="How AutoBE processes your packs internally", bg='#0A0A0A', fg='#9333ea',
                  font=("Segoe UI", 11, "bold"), anchor='w').pack(fill='x', padx=12, pady=(12, 6))
        internals = [
            "• Reads pack manifests and detects subpacks/scripts/dependencies.",
            "• Optionally prompts for subpack choice and repacks selected variant.",
            "• Merges pack content and normalizes output structure.",
            "• Writes merge manifest used by linked-pack remove/re-merge flow.",
            "• Builds final behavior_pack.mcpack and resource_pack.mcpack artifacts.",
        ]
        for line in internals:
            _tk.Label(internals_card, text=line, bg='#0A0A0A', fg='#CCCCCC', font=("Segoe UI", 10),
                      anchor='w', justify='left', wraplength=680).pack(fill='x', padx=12, pady=(0, 4))
        _tk.Label(internals_card, text="Note: if any step fails, read the error, fix inputs, and run merge again from clean output.",
                  bg='#0A0A0A', fg='#9ca3af', font=("Segoe UI", 9), anchor='w', justify='left', wraplength=680).pack(fill='x', padx=12, pady=(8, 12))
        
        return section_frame
    
    def _create_disclaimer_section(self):
        """Create the Important Notes section."""
        section_frame = _tk.Frame(self.help_content_frame, bg='#000000')
        
        disclaimer_card = _tk.LabelFrame(section_frame, text="📋 " + _("help.important_notes_full"), 
                                         bg='#1a1a1a', fg='#FFFFFF', font=("Segoe UI", 14, "bold"),
                                         relief='flat', bd=0)
        disclaimer_card.pack(fill='both', expand=True, padx=0, pady=(0, 15))
        
        disclaimer_inner = _tk.Frame(disclaimer_card, bg='#1a1a1a')
        disclaimer_inner.pack(fill='both', expand=True, padx=20, pady=15)
        
        disclaimer_items = [
            (_("help.disc1_title"), _("help.disc1_desc")),
            (_("help.disc2_title"), _("help.disc2_desc")),
            (_("help.disc3_title"), _("help.disc3_desc")),
            (_("help.disc4_title"), _("help.disc4_desc")),
        ]
        
        for title, description in disclaimer_items:
            item_frame = _tk.Frame(disclaimer_inner, bg='#0A0A0A', relief='flat')
            item_frame.pack(fill='x', pady=(0, 12), padx=5)
            
            item_title = _tk.Label(item_frame, text=f"• {title}", bg='#0A0A0A', fg='#9333ea',
                                  font=("Segoe UI", 11, "bold"), anchor='w', wraplength=600)
            item_title.pack(fill='x', padx=12, pady=(12, 6))
            
            item_desc = _tk.Label(item_frame, text=description, bg='#0A0A0A', fg='#CCCCCC',
                                 font=("Segoe UI", 10), anchor='w', justify='left', wraplength=600)
            item_desc.pack(fill='x', padx=12, pady=(0, 12))
        
        # Footer
        footer_label = _tk.Label(section_frame, text=_("app.codenex"), 
                                 bg='#000000', fg='#666666', font=("Segoe UI", 9))
        footer_label.pack(fill='x', pady=(10, 20))
        
        return section_frame
