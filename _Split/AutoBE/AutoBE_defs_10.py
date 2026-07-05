class AutoBEApp:

    def _show_import_panel(self, imported, error=None):
        """Show an in-window styled card for auto-import results (replaces popup)."""
        # Remove any previous import panel
        existing = getattr(self, '_import_panel_overlay', None)
        if existing:
            try:
                existing.destroy()
            except Exception:
                pass

        is_error = bool(error)
        accent   = '#ef4444' if is_error else '#9333ea'

        # Full-window dim overlay
        overlay = _tk.Frame(self._root, bg='#0a0a0a')
        overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        self._import_panel_overlay = overlay

        # Centered card
        card = _tk.Frame(overlay, bg='#1a1a1a', relief='flat', bd=0)
        card.place(relx=0.5, rely=0.5, anchor='center')

        # Top accent border
        _tk.Frame(card, bg=accent, height=3).pack(fill='x')

        inner = _tk.Frame(card, bg='#1a1a1a')
        inner.pack(fill='both', expand=True, padx=28, pady=24)

        # Icon + title row
        icon  = '✗' if is_error else '✓'
        title = 'Import Failed' if is_error else f'Imported {len(imported)} pack(s) to Minecraft Bedrock'
        title_row = _tk.Frame(inner, bg='#1a1a1a')
        title_row.pack(fill='x', pady=(0, 14))
        _tk.Label(title_row, text=icon, bg='#1a1a1a', fg=accent,
                  font=('Segoe UI', 20, 'bold')).pack(side='left', padx=(0, 10))
        _tk.Label(title_row, text=title, bg='#1a1a1a', fg='#FFFFFF',
                  font=('Segoe UI', 13, 'bold'), wraplength=380, justify='left').pack(side='left', fill='x', expand=True)

        if not is_error:
            # Compact BP/RP color legend
            leg = _tk.Frame(inner, bg='#111111', highlightthickness=1, highlightbackground='#2d2d2d')
            leg.pack(fill='x', pady=(0, 10))
            _tk.Label(leg, text='  Color key:', bg='#111111', fg='#999999',
                      font=('Segoe UI', 9, 'bold')).pack(side='left', padx=(8, 4), pady=5)
            for dot_col, dot_lbl in [('#a78bfa', 'Behavior Pack'), ('#34d399', 'Resource Pack')]:
                sw = _tk.Frame(leg, bg=dot_col, width=10, height=10)
                sw.pack(side='left', padx=(6, 2))
                sw.pack_propagate(False)
                _tk.Label(leg, text=dot_lbl, bg='#111111', fg='#d1d5db',
                          font=('Segoe UI', 9)).pack(side='left', padx=(0, 12), pady=5)

        if is_error:
            _tk.Label(inner, text=error, bg='#1a1a1a', fg='#999999',
                      font=('Segoe UI', 10), wraplength=400, justify='left').pack(anchor='w', pady=(0, 16))
        else:
            # Scrollable pack list
            list_outer = _tk.Frame(inner, bg='#111111', highlightthickness=1, highlightbackground='#2d2d2d')
            list_outer.pack(fill='x', pady=(0, 16))
            scroll = _tk.Scrollbar(list_outer, orient='vertical', bg='#1a1a1a',
                                   troughcolor='#111111', activebackground='#9333ea')
            scroll.pack(side='right', fill='y')
            listbox = _tk.Listbox(list_outer, bg='#111111', fg='#d1d5db',
                                  font=('Segoe UI', 10), relief='flat', bd=0,
                                  selectbackground='#9333ea', selectforeground='#FFFFFF',
                                  activestyle='none', highlightthickness=0,
                                  height=min(len(imported), 10),
                                  yscrollcommand=scroll.set)
            listbox.pack(side='left', fill='both', expand=True, padx=10, pady=8)
            scroll.config(command=listbox.yview)
            for pack in imported:
                # colour BP/RP differently
                listbox.insert(_tk.END, f'  {pack}')
                tag_col = '#a78bfa' if pack.endswith('_BP') else '#34d399'
                listbox.itemconfig(_tk.END, fg=tag_col)

        # Dismiss button
        def _dismiss():
            try:
                overlay.destroy()
            except Exception:
                pass
        btn_frame = _tk.Frame(inner, bg='#1a1a1a')
        btn_frame.pack(fill='x')
        _tk.Button(btn_frame, text='Done', command=_dismiss,
                   bg=accent, fg='#FFFFFF', font=('Segoe UI', 10, 'bold'),
                   relief='flat', cursor='hand2', padx=24, pady=6,
                   activebackground='#7e22ce', activeforeground='#FFFFFF').pack(side='right')

        overlay.bind('<Button-1>', lambda e: _dismiss() if e.widget is overlay else None)

    def _select_output_dir(self):
        _dir_name = _filedialog.askdirectory()
        if _dir_name:
            self._output_dir_var.set(_dir_name)
            self._out_dir = _dir_name

    def _collect_merged_output_dirs(self, base_dir):
        """Return list of directories that contain behavior_pack.mcpack (this merge output and any version subdirs)."""
        dirs = []
        if _os.path.isfile(_os.path.join(base_dir, "behavior_pack.mcpack")):
            dirs.append(base_dir)
        for name in _os.listdir(base_dir):
            sub = _os.path.join(base_dir, name)
            if _os.path.isdir(sub) and _os.path.isfile(_os.path.join(sub, "behavior_pack.mcpack")):
                dirs.append(sub)
        return dirs

    def _show_customize_merged_pack_dialog(self, current_dir, remaining_dirs=None):
        """Show one popup to name/describe/icon/author this merged pack only. When Apply or Skip, close and show next if remaining_dirs."""
        remaining_dirs = remaining_dirs or []
        pack_label = _os.path.basename(current_dir)
        if not pack_label:
            pack_label = _os.path.basename(_os.path.dirname(current_dir)) or "merged pack"
        title = _("customize.title") if _("customize.title") != "customize.title" else "Name your merged pack"
        dlg = _tk.Toplevel(self._root)
        self._apply_window_icon(dlg)
        dlg.title(title + " — " + pack_label)
        dlg.configure(bg="#1a1a1a")
        dlg.transient(self._root)
        dlg.geometry("440x420")
        dlg.resizable(True, True)
        try:
            sw, sh = self._root.winfo_screenwidth(), self._root.winfo_screenheight()
            dlg.maxsize(sw, sh)
            dlg.update_idletasks()
            w, h = dlg.winfo_reqwidth(), dlg.winfo_reqheight()
            x = max(0, (sw - w) // 2)
            y = max(0, (sh - h) // 2)
            dlg.geometry(f"440x420+{x}+{y}")
        except Exception:
            pass
        main = _tk.Frame(dlg, bg="#1a1a1a", padx=24, pady=24)
        main.pack(fill="both", expand=True)
        main.grid_columnconfigure(1, weight=1)
        subtitle_lbl = _tk.Label(main, text=_f("customize.this_pack", pack=pack_label) if _("customize.this_pack") != "customize.this_pack" else "This merged pack only: " + pack_label, bg="#1a1a1a", fg="#9333ea", font=("Segoe UI", 10), wraplength=380)
        subtitle_lbl.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 12))
        def _on_customize_resize(event):
            try:
                if subtitle_lbl.winfo_exists():
                    subtitle_lbl.configure(wraplength=max(200, event.width - 80))
            except Exception:
                pass
        dlg.bind("<Configure>", _on_customize_resize)
        default_name = _("customize.default_name") if _("customize.default_name") != "customize.default_name" else "My Merged Pack"
        default_desc = _("customize.default_desc") if _("customize.default_desc") != "customize.default_desc" else "Merged with AutoBE"
        _tk.Label(main, text=_("customize.name"), bg="#1a1a1a", fg="#E5E7EB", font=("Segoe UI", 11, "bold")).grid(row=1, column=0, sticky="w", pady=(0, 6))
        name_var = _tk.StringVar(value=default_name)
        _tk.Entry(main, textvariable=name_var, bg="#0A0A0A", fg="#FFFFFF", font=("Segoe UI", 11), insertbackground="#a855f7", relief="flat").grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 16))
        _tk.Label(main, text=_("customize.description"), bg="#1a1a1a", fg="#E5E7EB", font=("Segoe UI", 11, "bold")).grid(row=3, column=0, sticky="w", pady=(0, 6))
        desc_var = _tk.StringVar(value=default_desc)
        _tk.Entry(main, textvariable=desc_var, bg="#0A0A0A", fg="#FFFFFF", font=("Segoe UI", 11), insertbackground="#a855f7", relief="flat").grid(row=4, column=0, columnspan=2, sticky="ew", pady=(0, 16))
        _tk.Label(main, text=_("customize.icon"), bg="#1a1a1a", fg="#E5E7EB", font=("Segoe UI", 11, "bold")).grid(row=5, column=0, sticky="w", pady=(0, 6))
        icon_path_var = _tk.StringVar(value="")
        icon_label = _tk.Label(main, text=_("customize.no_icon") if _("customize.no_icon") != "customize.no_icon" else "None", bg="#1a1a1a", fg="#999999", font=("Segoe UI", 10), anchor="w")
        icon_label.grid(row=6, column=0, columnspan=2, sticky="w", pady=(0, 16))

        def pick_icon():
            path = _filedialog.askopenfilename(title=_("customize.pick_icon") if _("customize.pick_icon") != "customize.pick_icon" else "Pick pack icon", filetypes=[("Images", "*.png *.jpg *.jpeg"), ("PNG", "*.png"), ("JPEG", "*.jpg *.jpeg"), ("All", "*")])
            if path:
                icon_path_var.set(path)
                icon_label.config(text=_os.path.basename(path), fg="#E5E7EB")

        _tk.Button(main, text=_("customize.browse_icon") if _("customize.browse_icon") != "customize.browse_icon" else "Browse...", command=pick_icon, bg="#3a3a3a", fg="#FFFFFF", font=("Segoe UI", 10), relief="flat", cursor="hand2", activebackground="#9333ea").grid(row=6, column=1, sticky="e", pady=(0, 16))
        _tk.Label(main, text=_("customize.author"), bg="#1a1a1a", fg="#E5E7EB", font=("Segoe UI", 11, "bold")).grid(row=7, column=0, sticky="w", pady=(0, 6))
        author_var = _tk.StringVar(value="")
        _tk.Entry(main, textvariable=author_var, bg="#0A0A0A", fg="#FFFFFF", font=("Segoe UI", 11), insertbackground="#a855f7", relief="flat").grid(row=8, column=0, columnspan=2, sticky="ew", pady=(0, 16))

        def apply_and_next():
            name = (name_var.get() or "").strip() or default_name
            desc = (desc_var.get() or "").strip() or default_desc
            icon_path = (icon_path_var.get() or "").strip()
            if not icon_path or not _os.path.isfile(icon_path):
                icon_path = None
            author = (author_var.get() or "").strip()
            bp_path = _os.path.join(current_dir, "behavior_pack.mcpack")
            rp_path = _os.path.join(current_dir, "resource_pack.mcpack")
            if _os.path.isfile(bp_path):
                self._update_mcpack_metadata(bp_path, name, desc, icon_path, author=author)
            if _os.path.isfile(rp_path):
                self._update_mcpack_metadata(rp_path, name, desc, icon_path, author=author)
            dlg.destroy()
            if remaining_dirs:
                self._root.after(50, lambda: self._show_customize_merged_pack_dialog(remaining_dirs[0], remaining_dirs[1:]))
            else:
                _messagebox.showinfo(_("customize.done_title") or "Done", _("customize.done_msg") if _("customize.done_msg") != "customize.done_msg" else "Pack name, description, icon, and author updated.")

        def skip_and_next():
            dlg.destroy()
            if remaining_dirs:
                self._root.after(50, lambda: self._show_customize_merged_pack_dialog(remaining_dirs[0], remaining_dirs[1:]))

        btn_frame = _tk.Frame(main, bg="#1a1a1a")
        btn_frame.grid(row=9, column=0, columnspan=2, pady=(20, 0))
        skip_text = _("customize.skip") if _("customize.skip") != "customize.skip" else "Skip"
        apply_text = _("customize.apply") if _("customize.apply") != "customize.apply" else "Apply"
        _tk.Button(btn_frame, text=skip_text, command=skip_and_next, bg="#3a3a3a", fg="#FFFFFF", font=("Segoe UI", 11), relief="flat", cursor="hand2", activebackground="#555", padx=20, pady=10).pack(side="left", padx=(0, 12))
        _tk.Button(btn_frame, text=apply_text, command=apply_and_next, bg="#9333ea", fg="#FFFFFF", font=("Segoe UI", 11, "bold"), relief="flat", cursor="hand2", activebackground="#a855f7", padx=20, pady=10).pack(side="left")

    def _load_merge_manifest(self, folder):
        """Load _autobe_merge_manifest.json from folder or its subdirs. Return (manifest_dict, manifest_folder) or (None, None)."""
        path = _os.path.join(folder, "_autobe_merge_manifest.json")
        if _os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return _json.load(f), folder
            except Exception:
                pass
        for name in _os.listdir(folder):
            sub = _os.path.join(folder, name)
            if _os.path.isdir(sub):
                path = _os.path.join(sub, "_autobe_merge_manifest.json")
                if _os.path.isfile(path):
                    try:
                        with open(path, "r", encoding="utf-8") as f:
                            return _json.load(f), sub
                    except Exception:
                        pass
        return None, None

    def _show_linked_packs_dialog(self, forced_output_dir=None):
        """Show dialog listing addons in the current merge; allow removing one and re-merging without it. If forced_output_dir is set, use it instead of UI output path."""
        out_dir = (forced_output_dir or "").strip() if forced_output_dir else None
        if not out_dir or not _os.path.isdir(out_dir):
            out_dir = (self._output_dir_var.get() or "").strip()
        if not out_dir or not _os.path.isdir(out_dir):
            out_dir = _filedialog.askdirectory(title=_("linked.select_output") if _("linked.select_output") != "linked.select_output" else "Select merged output folder")
        if not out_dir:
            return
        manifest_data, manifest_folder = self._load_merge_manifest(out_dir)
        if not manifest_data:
            _messagebox.showinfo(
                _("linked.no_manifest_title") if _("linked.no_manifest_title") != "linked.no_manifest_title" else "Linked packs",
                _("linked.no_manifest_msg") if _("linked.no_manifest_msg") != "linked.no_manifest_msg" else "No merge manifest found in this folder. Run a merge first, then use Linked packs to view or remove addons."
            )
            return
        source_packs = manifest_data.get("source_packs") or []
        output_dir = manifest_data.get("output_dir") or manifest_folder
        if not source_packs:
            _messagebox.showinfo(_("linked.no_manifest_title") or "Linked packs", _("linked.no_packs_in_manifest") or "No source packs listed in manifest.")
            return
        dlg = _tk.Toplevel(self._root)
        self._apply_window_icon(dlg)
        dlg.title(_("linked.title") if _("linked.title") != "linked.title" else "Linked packs")
        dlg.configure(bg="#1a1a1a")
        dlg.transient(self._root)
        dlg.geometry("420x380")
        dlg.resizable(True, True)
        try:
            sw, sh = self._root.winfo_screenwidth(), self._root.winfo_screenheight()
            dlg.maxsize(sw, sh)
            dlg.update_idletasks()
            w, h = dlg.winfo_reqwidth(), dlg.winfo_reqheight()
            x = max(0, (sw - w) // 2)
            y = max(0, (sh - h) // 2)
            dlg.geometry(f"420x380+{x}+{y}")
        except Exception:
            pass
        main = _tk.Frame(dlg, bg="#1a1a1a", padx=20, pady=20)
        main.pack(fill="both", expand=True)
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(1, weight=1)
        linked_desc_lbl = _tk.Label(main, text=_("linked.desc") if _("linked.desc") != "linked.desc" else "Addons in this merge. Remove one to re-merge without it.", bg="#1a1a1a", fg="#E5E7EB", font=("Segoe UI", 11), wraplength=380, justify="left")
        linked_desc_lbl.grid(row=0, column=0, sticky="w", pady=(0, 12))
        def _on_linked_resize(event):
            try:
                if linked_desc_lbl.winfo_exists():
                    linked_desc_lbl.configure(wraplength=max(200, event.width - 80))
            except Exception:
                pass
        dlg.bind("<Configure>", _on_linked_resize)
        list_frame = _tk.Frame(main, bg="#0A0A0A", highlightthickness=1, highlightbackground="#404040")
        list_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 12))
        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(0, weight=1)
        canvas = _tk.Canvas(list_frame, bg="#0A0A0A", highlightthickness=0)
        canvas.grid(row=0, column=0, sticky="nsew")
        inner = _tk.Frame(canvas, bg="#0A0A0A")
        inner.grid_columnconfigure(0, weight=1)
        canvas_window = canvas.create_window(0, 0, window=inner, anchor="nw")
        def _on_configure(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(canvas_window, width=e.width)
        inner.bind("<Configure>", _on_configure)
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_window, width=e.width))
        def _on_wheel(e):
            canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        def _enter(e):
            canvas.bind_all("<MouseWheel>", _on_wheel)
        def _leave(e):
            try:
                canvas.unbind_all("<MouseWheel>")
            except Exception:
                pass
        canvas.bind("<Enter>", _enter)
        canvas.bind("<Leave>", _leave)
        inner.bind("<Enter>", _enter)
        inner.bind("<Leave>", _leave)
        remove_btn_vars = []
        for i, path in enumerate(source_packs):
            row = _tk.Frame(inner, bg="#1a1a1a", height=40)
            row.grid(row=i, column=0, sticky="ew", padx=8, pady=4)
            row.grid_columnconfigure(0, weight=1)
            name = _os.path.basename(path)
            if len(name) > 45:
                name = name[:42] + "…"
            _tk.Label(row, text=name, bg="#1a1a1a", fg="#FFFFFF", font=("Segoe UI", 10), anchor="w").grid(row=0, column=0, sticky="w", padx=8, pady=8)
            remove_text = _("linked.remove") if _("linked.remove") != "linked.remove" else "Remove"
            btn = _tk.Button(row, text=remove_text, command=lambda p=path: _do_remove(p), bg="#7f1d1d", fg="#FFFFFF", font=("Segoe UI", 9), relief="flat", cursor="hand2", activebackground="#991b1b")
            btn.grid(row=0, column=1, padx=8, pady=6)
            remove_btn_vars.append((path, btn))

        def _do_remove(path_to_remove):
            confirm_msg = _("linked.remove_confirm") if _("linked.remove_confirm") != "linked.remove_confirm" else "Remove this addon from the merge? The pack will be re-merged without it (output will be overwritten)."
            if not _messagebox.askyesno(_("linked.remove_confirm_title") or "Remove addon", confirm_msg):
                return
            remaining = [p for p in source_packs if p != path_to_remove]
            existing = [p for p in remaining if _os.path.isfile(p)]
            if not existing:
                _messagebox.showerror(_("msg.error"), _("linked.cannot_remove_only") if _("linked.cannot_remove_only") != "linked.cannot_remove_only" else "Need at least one pack remaining.")
                return
            if len(existing) < len(remaining):
                _messagebox.showwarning(_("linked.missing_title") or "Some files missing", _("linked.missing_msg") if _("linked.missing_msg") != "linked.missing_msg" else "Some original packs were moved or deleted; only existing paths will be used.")
            dlg.destroy()
            self._files = existing
            self._output_dir_var.set(output_dir)
            self._out_dir = output_dir
            self._file_list_data = [(_os.path.basename(p), p, None, None) for p in existing]
            self._file_paths = {_os.path.basename(p): p for p in existing}
            self._rebuild_autobe_file_list()
            self._file_count_label.config(text=_f("app.files_selected", n=len(existing)))
            self._process_and_create_manifest()

        _tk.Button(main, text=_("common.close"), command=dlg.destroy, bg="#3a3a3a", fg="#FFFFFF", font=("Segoe UI", 11), relief="flat", cursor="hand2", activebackground="#9333ea", padx=20, pady=10).grid(row=2, column=0, pady=(0, 0))

    def _update_mcpack_metadata(self, mcpack_path, name, description, icon_path=None, author=None):
        """Update manifest name/description/author and optionally pack_icon in an existing .mcpack zip."""
        if not _os.path.isfile(mcpack_path):
            return
        try:
            with _zipfile.ZipFile(mcpack_path, 'r') as zf:
                namelist = zf.namelist()
                manifest_name = None
                for n in namelist:
                    if n.lower().endswith('manifest.json'):
                        manifest_name = n
                        break
                if not manifest_name:
                    return
                manifest_bytes = zf.read(manifest_name)
            try:
                manifest = _json.loads(manifest_bytes.decode('utf-8'))
            except Exception:
                return
            header = manifest.get('header') or {}
            header['name'] = name
            header['description'] = description
            manifest['header'] = header
            modules = manifest.get('modules') or []
            if modules and isinstance(modules[0], dict):
                modules[0]['description'] = description
            manifest['modules'] = modules
            if author is not None:
                meta = manifest.get('metadata') or {}
                manifest['metadata'] = meta
                meta['authors'] = [author] if author.strip() else []
            new_manifest_bytes = _json.dumps(manifest, indent=2).encode('utf-8')
            icon_ext = None
            if icon_path and _os.path.isfile(icon_path):
                icon_ext = _os.path.splitext(icon_path)[1].lower()
                if icon_ext not in ('.png', '.jpg', '.jpeg'):
                    icon_ext = '.png'
            tmp_path = mcpack_path + '.autobe_tmp'
            with _zipfile.ZipFile(tmp_path, 'w', _zipfile.ZIP_DEFLATED) as zout:
                with _zipfile.ZipFile(mcpack_path, 'r') as zf:
                    for item in zf.namelist():
                        if item == manifest_name:
                            zout.writestr(item, new_manifest_bytes)
                        elif icon_ext and item.lower().endswith(('pack_icon.png', 'pack_icon.jpg', 'pack_icon.jpeg')):
                            continue
                        else:
                            zout.writestr(item, zf.read(item))
                if icon_path and _os.path.isfile(icon_path):
                    with open(icon_path, 'rb') as f:
                        icon_data = f.read()
                    icon_basename = 'pack_icon.png' if icon_ext in ('.png',) or not icon_ext else 'pack_icon' + icon_ext
                    prefix = _os.path.dirname(manifest_name)
                    out_icon_name = (_os.path.join(prefix, icon_basename).replace('\\', '/')) if prefix else icon_basename
                    zout.writestr(out_icon_name, icon_data)
            _os.replace(tmp_path, mcpack_path)
        except Exception as e:
            _logging.warning(f"Could not update mcpack metadata {mcpack_path}: {e}")

    def _process_and_create_manifest(self):
        if not self._files:
            _messagebox.showerror(_("msg.error"), _("process.select_mcpacks_only"))
            _logging.error("No .mcpack files selected")
            return
        if not self._out_dir:
            _messagebox.showerror(_("msg.error"), _("process.select_output"))
            _logging.error("No output directory selected")
            return

        if not self._validate_files():
            return

        # Disable start button during processing
        self._btn_start.config(state='disabled')
        
        # Run processing in a separate thread to prevent UI freezing
        def process_thread():
            try:
                self._root.after(0, lambda: self._reset_progress())
                self._root.after(0, lambda: self._update_progress(0, 0, "Initializing process..."))
                _logging.info("=== AutoBE merge started ===")
                _logging.info(f"  Files selected: {len(self._files)}")
                _logging.info(f"  Output dir: {self._out_dir}")
                merge_by_version = getattr(self, "merge_by_version_var", None) and self.merge_by_version_var.get()
                _logging.info(f"  Merge by version: {merge_by_version}")
                customize_base = self._out_dir
                if merge_by_version:
                    _logging.info("Grouping files by script API version...")
                    groups = self._group_files_by_script_api_version(self._files)
                    if not groups:
                        _logging.error("No valid mcpack groups found — aborting.")
                        self._root.after(0, lambda: _messagebox.showerror(_("msg.error"), _("process.no_valid_mcpacks")))
                        return
                    _logging.info(f"  Groups found: { {k: len(v) for k, v in groups.items()} }")
                    # Separate groups into: packs needing Preview Minecraft vs
                    # packs that only need the Beta APIs toggle in stable Bedrock.
                    _preview_groups   = {k: v for k, v in groups.items()
                                         if 'preview' in k.lower() and k != 'none'}
                    _beta_alpha_groups = {k: v for k, v in groups.items()
                                          if any(s in k.lower() for s in ('beta', 'alpha', 'rc'))
                                          and 'preview' not in k.lower() and k != 'none'}
                    _has_stable = any(
                        k != 'none' and not any(s in k.lower() for s in ('beta', 'alpha', 'rc', 'preview'))
                        for k in groups)

                    if _preview_groups or _beta_alpha_groups:
                        _notice_lines = []

                        if _preview_groups:
                            _notice_lines += [
                                "Some of your addons require the PREVIEW version of",
                                "Minecraft Bedrock (the separate Preview app / channel).",
                                "They will NOT work in stable Bedrock.",
                                "",
                                "Addons that require Minecraft Preview:",
                            ]
                            for _pk, _pv in _preview_groups.items():
                                _notice_lines.append(f"  Script API: {_pk.replace('_', '.')}")
                                for _pf in _pv:
                                    _notice_lines.append(f"    \u2022 {_os.path.basename(_pf)}")
                            _notice_lines.append("")

                        if _beta_alpha_groups:
                            if _preview_groups:
                                _notice_lines += [
                                    "─" * 52,
                                    "",
                                ]
                            _multi = len(groups) > 1
                            _notice_lines += [
                                "Some of your addons use Experimental Script APIs",
                                "(versions ending in -beta or -alpha in their manifest).",
                                "",
                                "These work fine in STABLE Minecraft Bedrock —",
                                "just enable  \"Beta APIs\"  in your world's Experiments",
                                "before applying the packs.",
                            ]
                            if _multi:
                                _notice_lines += [
                                    "",
                                    "AutoBE places each API version in its own output",
                                    "subfolder. Apply ALL subfolders to the same world",
                                    "with Beta APIs ON.",
                                ]
                            _notice_lines += [
                                "",
                                "Addons that need the Beta APIs toggle:",
                            ]
                            for _bk, _bv in _beta_alpha_groups.items():
                                _notice_lines.append(f"  Script API: {_bk.replace('_', '.')}")
                                for _bf in _bv:
                                    _notice_lines.append(f"    \u2022 {_os.path.basename(_bf)}")
                            _notice_lines += [
                                "",
                                "How to enable: Edit World \u2192 Experiments \u2192 Beta APIs \u2192 ON.",
                                "Without it those addons' scripts will not run.",
                            ]

                        _notice_text = "\n".join(_notice_lines)
                        _has_preview_only = bool(_preview_groups) and not bool(_beta_alpha_groups)
                        _beta_done = threading.Event()
                        def _show_beta_warn(_bt=_notice_text, _prev=_has_preview_only):
                            try:
                                _win = _tk.Toplevel(self._root)
                                if _prev:
                                    _win.title("Preview Version Required")
                                    _hdr = "\u26a0  Minecraft Preview Required"
                                    _sub = "These addons require the separate Minecraft Preview app — they won't run in stable Bedrock."
                                elif _preview_groups:
                                    _win.title("Script API Notice")
                                    _hdr = "\u26a0  Preview + Beta API Addons Detected"
                                    _sub = "See details below for which addons need Preview and which only need the Beta APIs toggle."
                                else:
                                    _win.title("Beta APIs Required")
                                    _hdr = "⚠ Beta APIs Required"
                                    _sub = "Some addons use experimental features. Enable Beta APIs in your world settings before applying these packs."
                                _win.configure(bg='#1a1a2e')
                                _win.resizable(False, False)
                                _win.grab_set()
                                _win.lift()
                                
                                # Main container with padding
                                _container = _tk.Frame(_win, bg='#1a1a2e')
                                _container.pack(padx=32, pady=32, fill='both', expand=True)
                                
                                # Header with icon
                                _tk.Label(_container, text=_hdr,
                                          bg='#1a1a2e', fg='#f97316',
                                          font=("Segoe UI", 14, "bold")).pack(pady=(0, 12))
                                
                                # Subtitle with better spacing
                                _tk.Label(_container, text=_sub,
                                          bg='#1a1a2e', fg='#cbd5e1',
                                          font=("Segoe UI", 10), wraplength=500, justify='center').pack(pady=(0, 20))
                                
                                # Info box with border
                                _info_frame = _tk.Frame(_container, bg='#16213e', relief='solid', borderwidth=1)
                                _info_frame.pack(fill='both', expand=True, pady=(0, 20))
                                
                                _txt = _tk.Text(_info_frame, bg='#16213e', fg='#e2e8f0',
                                                font=("Consolas", 9), relief='flat',
                                                width=58, height=12, wrap='word',
                                                padx=12, pady=12)
                                _txt.insert('1.0', _bt)
                                _txt.configure(state='disabled')
                                _txt.pack(fill='both', expand=True, padx=1, pady=1)
                                
                                # Modern button with hover effect
                                _btn = _tk.Button(_container, text="Continue",
                                                   bg='#f97316', fg='#ffffff',
                                                   font=("Segoe UI", 10, "bold"), relief='flat',
                                                   padx=24, pady=10, cursor='hand2',
                                                   activebackground='#ea580c', activeforeground='#ffffff',
                                                   command=lambda: (_win.destroy(), _beta_done.set()))
                                _btn.pack(pady=(0, 0))
                                _win.protocol("WM_DELETE_WINDOW",
                                              lambda: (_win.destroy(), _beta_done.set()))
                            except Exception:
                                _beta_done.set()
                        self._root.after(0, _show_beta_warn)
                        _beta_done.wait()
                    original_out = self._out_dir
                    customize_base = original_out
                    # Store original files for Discord merge log (all groups combined)
                    original_files_all = list(self._files)
                    for folder_key, group_files in sorted(groups.items(), key=lambda x: (x[0] != 'none', x[0])):
                        _logging.info(f"  Processing group '{folder_key}' ({len(group_files)} files)...")
                        self._files = list(group_files)
                        self._out_dir = _os.path.join(original_out, folder_key)
                        _os.makedirs(self._out_dir, exist_ok=True)
                        self._start_process()
                        _logging.info(f"  Group '{folder_key}' done.")
                        _bp_mcpack = _os.path.join(self._out_dir, 'behavior_pack.mcpack')
                        _rp_mcpack = _os.path.join(self._out_dir, 'resource_pack.mcpack')
                    # Unify player.json across all groups so every RP has the same
                    # comprehensive player entity (animations + variables from all groups).
                    try:
                        self._unify_cross_group_player_json(original_out)
                    except Exception:
                        pass
                    # Unify player animation / animation-controller / render-controller files
                    # across all groups.  Play-as-Link lands in the 'none' group with 35 custom
                    # player animations; without this step Bedrock only honours the highest-priority
                    # RP's player.animation.json, silently discarding all the other groups' files.
                    try:
                        self._unify_cross_group_player_anims(original_out)
                    except Exception as _e:
                        _logging.error(f"[_unify_cross_group_player_anims] Failed: {_e}", exc_info=True)
                    # Unify terrain_texture.json / item_texture.json / blocks.json across all
                    # groups so custom block texture registrations from one group's RP (e.g.
                    # QB Furniture's warped_planks entry in 2_x RP) are present in every
                    # group's RP.  Without this, Bedrock may fail to resolve texture IDs for
                    # blocks whose BP is in a lower-priority group, showing them as dirt.
                    try:
                        self._unify_cross_group_atlas_files(original_out)
                    except Exception:
                        pass
                    # Unify hud_screen.json / _ui_defs.json across all groups so every RP
                    # carries the full set of HUD patches (e.g. temperature + mqps patches
                    # survive alongside Paraglider's dominant 150 KB hud_screen).
                    try:
                        self._unify_cross_group_hud_files(original_out)
                    except Exception:
                        pass
                    # Bake the merged root hud_screen.json into every subpack variant.
                    # Subpacks like SWAILA's position variants (topleft / topright / …) each
                    # carry their own hud_screen.json that REPLACES the root when selected,
                    # silently discarding mqps / temperature / Paraglider HUD changes.  This
                    # step merges the complete root hud_screen into each subpack so all HUD
                    # elements survive regardless of which position the user picks.
                    try:
                        self._merge_subpack_hud_files(original_out)
                    except Exception:
                        pass
                    # Send Discord merge log with ALL selected addons (not just current group)
                    try:
                        self._send_discord_merge_log(original_files_all)
                    except Exception as _e:
                        _logging.warning(f"Could not send Discord merge log: {_e}")
                    self._root.after(0, lambda: self._update_progress(4, 100, "All steps completed successfully! ✓"))
                    if getattr(self, '_auto_import_var', None) and self._auto_import_var.get():
                        self._import_to_minecraft(original_out)
                else:
                    _logging.info("Starting single-group merge...")
                    self._start_process()
                    _logging.info("Single-group merge done.")
                    _bp_mcpack_sg = _os.path.join(self._out_dir, 'behavior_pack.mcpack')
                    _rp_mcpack_sg = _os.path.join(self._out_dir, 'resource_pack.mcpack')
                    # Send Discord merge log with all selected addons (single-group case)
                    try:
                        self._send_discord_merge_log(self._files)
                    except Exception as _e:
                        _logging.warning(f"Could not send Discord merge log: {_e}")
                    self._root.after(0, lambda: self._update_progress(4, 100, "All steps completed successfully! ✓"))
                    if getattr(self, '_auto_import_var', None) and self._auto_import_var.get():
                        self._import_to_minecraft(self._out_dir)
                # Reset memory and clear the list on main thread
                self._root.after(0, lambda: self._reset_file_list())
                if getattr(self, "customize_pack_after_merge_var", None) and self.customize_pack_after_merge_var.get() and customize_base and _os.path.isdir(customize_base):
                    _dirs = self._collect_merged_output_dirs(customize_base)
                    if _dirs:
                        self._root.after(100, lambda: self._show_customize_merged_pack_dialog(_dirs[0], _dirs[1:]))
                if getattr(self, "show_linked_packs_after_merge_var", None) and self.show_linked_packs_after_merge_var.get() and customize_base and _os.path.isdir(customize_base):
                    self._root.after(600, lambda b=customize_base: self._show_linked_packs_dialog(forced_output_dir=b))
                # Excel organization after merge
                if getattr(self, "modpack_organization_var", None) and self.modpack_organization_var.get() and _EXCEL_MANAGER:
                    # Use original_files_all for script version merge, self._files for single group
                    files_to_use = original_files_all if groups else self._files
                    self._root.after(1000, lambda: self._handle_excel_organization(customize_base, files_to_use))
            except Exception as _e:
                log_error(_e)
                _logging.error("An error occurred during the process", exc_info=True)
                self._root.after(0, lambda: _messagebox.showerror(_("msg.error"), _f("process.an_error_occurred", error=_e)))
            finally:
                # Re-enable start button
                self._root.after(0, lambda: self._btn_start.config(state='normal'))
                # Always clean up any _modified.mcpack temp files — handles cancel, crash, early exit
                for _mf in getattr(self, '_pending_cleanup_mcpacks', []):
                    try:
                        if _os.path.exists(_mf):
                            _os.remove(_mf)
                    except Exception:
                        pass
                self._pending_cleanup_mcpacks = []
        
        threading.Thread(target=process_thread, daemon=True).start()
    
    def _handle_excel_organization(self, output_dir: str, source_files: list):
        """Handle Excel/CSV organization after merge - prompt for modpack name and create Excel/CSV sheet."""
        if not _EXCEL_MANAGER:
            _logging.warning("Excel/CSV functionality not available")
            return
        
        if not source_files:
            _logging.warning("No source files provided for Excel organization")
            return
        
        _logging.info(f"Opening Excel organization dialog with {len(source_files)} files")
        
        # Create dialog to get modpack name
        dialog = _tk.Toplevel(self._root)
        dialog.title("Modpack Organization")
        dialog.configure(bg='#1a1a1a')
        dialog.transient(self._root)
        dialog.grab_set()
        dialog.attributes('-topmost', True)  # Force dialog to be on top
        
        # Main container with padding
        main_frame = _tk.Frame(dialog, bg='#1a1a1a')
        main_frame.pack(fill='both', expand=True, padx=30, pady=30)
        
        # Title
        _tk.Label(main_frame, text="Modpack Organization", bg='#1a1a1a', fg='#FFFFFF',
                 font=("Segoe UI", 16, "bold")).pack(pady=(0, 15))
        
        # Description
        _tk.Label(main_frame, text="Name your modpack to organize addons in Excel/CSV", bg='#1a1a1a', fg='#CCCCCC',
                 font=("Segoe UI", 10)).pack(pady=(0, 20))
        
        # Modpack name input
        _tk.Label(main_frame, text="Modpack Name:", bg='#1a1a1a', fg='#FFFFFF',
                 font=("Segoe UI", 11)).pack(pady=(0, 5), anchor='w')
        
        name_var = _tk.StringVar()
        name_entry = _tk.Entry(main_frame, textvariable=name_var, width=45, bg='#0A0A0A', fg='#FFFFFF',
                              font=("Segoe UI", 11), insertbackground='#9333ea', relief='flat',
                              highlightthickness=1, highlightbackground='#1a1a1a', highlightcolor='#9333ea')
        name_entry.pack(pady=(0, 20), fill='x')
        name_entry.focus()
        
        # Version inputs
        version_frame = _tk.Frame(main_frame, bg='#1a1a1a')
        version_frame.pack(pady=(0, 20), fill='x')
        
        _tk.Label(version_frame, text="Min Version:", bg='#1a1a1a', fg='#FFFFFF',
                 font=("Segoe UI", 10)).grid(row=0, column=0, padx=(0, 10), pady=5, sticky='w')
        min_var = _tk.StringVar(value="1.21.0")
        _tk.Entry(version_frame, textvariable=min_var, width=20, bg='#0A0A0A', fg='#FFFFFF',
                 font=("Segoe UI", 10), relief='flat').grid(row=0, column=1, pady=5, sticky='w')
        
        _tk.Label(version_frame, text="Max Version:", bg='#1a1a1a', fg='#FFFFFF',
                 font=("Segoe UI", 10)).grid(row=1, column=0, padx=(0, 10), pady=5, sticky='w')
        max_var = _tk.StringVar(value="1.21.90")
        _tk.Entry(version_frame, textvariable=max_var, width=20, bg='#0A0A0A', fg='#FFFFFF',
                 font=("Segoe UI", 10), relief='flat').grid(row=1, column=1, pady=5, sticky='w')
        
        # Buttons
        button_frame = _tk.Frame(main_frame, bg='#1a1a1a')
        button_frame.pack(pady=(10, 0))
        
        def create_excel():
            modpack_name = name_var.get().strip()
            if not modpack_name:
                _messagebox.showerror("Error", "Please enter a modpack name")
                return
            
            try:
                # Extract addon info from source files
                addons = []
                for file_path in source_files:
                    addon_name = _os.path.basename(file_path)
                    # Try to get version from manifest
                    version = "Unknown"
                    try:
                        manifest = self._get_manifest_data(file_path)
                        if manifest and 'header' in manifest:
                            version = manifest['header'].get('version', 'Unknown')
                    except:
                        pass
                    
                    addons.append({
                        "name": addon_name,
                        "path": file_path,
                        "version": version,
                        "min_version": min_var.get(),
                        "max_version": max_var.get(),
                        "status": "Active",
                        "notes": ""
                    })
                
                # Create Excel sheet
                _EXCEL_MANAGER.create_new_workbook()
                _EXCEL_MANAGER.add_modpack_sheet(
                    modpack_name,
                    addons,
                    min_version=min_var.get(),
                    max_version=max_var.get()
                )
                
                # Save Excel/CSV file
                extension = ".csv" if _EXCEL_MANAGER.csv_mode else ".xlsx"
                excel_path = _os.path.join(output_dir, f"{modpack_name}_config{extension}")
                _EXCEL_MANAGER.save_workbook(excel_path)
                
                _messagebox.showinfo("Success", f"Modpack configuration saved to:\n{excel_path}")
                dialog.destroy()
                
            except Exception as e:
                _logging.error(f"Error creating Excel/CSV file: {e}")
                _messagebox.showerror("Error", f"Failed to create Excel/CSV file:\n{e}")
        
        def cancel():
            dialog.destroy()
        
        _tk.Button(button_frame, text="Create Excel/CSV", command=create_excel, bg='#9333ea', fg='#FFFFFF',
                  font=("Segoe UI", 11, "bold"), relief='flat', cursor='hand2', activebackground='#a855f7',
                  padx=20, pady=8).pack(side='left', padx=(0, 10))
        
        _tk.Button(button_frame, text="Cancel", command=cancel, bg='#1a1a1a', fg='#FFFFFF',
                  font=("Segoe UI", 11), relief='flat', cursor='hand2', activebackground='#2d2d2d',
                  padx=20, pady=8).pack(side='left')
        
        # Center dialog after all content is packed
        dialog.update_idletasks()
        width = dialog.winfo_reqwidth()
        height = dialog.winfo_reqheight()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")
        dialog.minsize(width, height)
    
    def _show_excel_manager(self):
        """Show Excel/CSV manager dialog for manual organization of modpacks."""
        if not _EXCEL_MANAGER:
            _messagebox.showerror("Error", "Excel/CSV functionality is not available")
            return
        
        dialog = _tk.Toplevel(self._root)
        dialog.title("Excel/CSV Modpack Manager")
        dialog.geometry("900x600")
        dialog.configure(bg='#1a1a1a')
        dialog.transient(self._root)
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (900 // 2)
        y = (dialog.winfo_screenheight() // 2) - (600 // 2)
        dialog.geometry(f"900x600+{x}+{y}")
        
        # Title
        _tk.Label(dialog, text="📊 Excel/CSV Modpack Manager", bg='#1a1a1a', fg='#FFFFFF',
                 font=("Segoe UI", 16, "bold")).pack(pady=(20, 10))
        
        # Description
        _tk.Label(dialog, text="Load Excel/CSV files to manage your modpacks manually", bg='#1a1a1a', fg='#CCCCCC',
                 font=("Segoe UI", 10)).pack(pady=(0, 20))
        
        # Main content frame
        content_frame = _tk.Frame(dialog, bg='#1a1a1a')
        content_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_rowconfigure(1, weight=1)
        
        # File selection frame
        file_frame = _tk.Frame(content_frame, bg='#1a1a1a')
        file_frame.grid(row=0, column=0, sticky='ew', pady=(0, 10))
        
        _tk.Label(file_frame, text="Excel/CSV File:", bg='#1a1a1a', fg='#FFFFFF',
                 font=("Segoe UI", 11)).pack(side='left', padx=(0, 10))
        
        excel_path_var = _tk.StringVar()
        excel_entry = _tk.Entry(file_frame, textvariable=excel_path_var, width=50, bg='#0A0A0A', fg='#FFFFFF',
                              font=("Segoe UI", 10), relief='flat')
        excel_entry.pack(side='left', padx=(0, 10))
        
        def browse_excel():
            file_path = _filedialog.askopenfilename(
                title="Select Excel/CSV File",
                filetypes=[("Excel/CSV Files", "*.xlsx;*.csv"), ("Excel Files", "*.xlsx"), ("CSV Files", "*.csv"), ("All Files", "*.*")]
            )
            if file_path:
                excel_path_var.set(file_path)
                load_excel_file(file_path)
        
        _tk.Button(file_frame, text="Browse", command=browse_excel, bg='#9333ea', fg='#FFFFFF',
                  font=("Segoe UI", 10), relief='flat', cursor='hand2').pack(side='left', padx=(0, 10))
        
        def create_new_excel():
            _EXCEL_MANAGER.create_new_workbook()
            _messagebox.showinfo("Success", "New Excel workbook created. Save it to continue.")
            save_excel_file()
        
        _tk.Button(file_frame, text="New", command=create_new_excel, bg='#10b981', fg='#FFFFFF',
                  font=("Segoe UI", 10), relief='flat', cursor='hand2').pack(side='left')
        
        # Modpack list frame
        list_frame = _tk.LabelFrame(content_frame, text="Modpacks", bg='#1a1a1a', fg='#FFFFFF',
                                    font=("Segoe UI", 11, "bold"))
        list_frame.grid(row=1, column=0, sticky='nsew')
        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(0, weight=1)
        
        # Listbox with scrollbar
        listbox_frame = _tk.Frame(list_frame, bg='#1a1a1a')
        listbox_frame.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)
        
        modpack_listbox = _tk.Listbox(listbox_frame, bg='#0A0A0A', fg='#FFFFFF', font=("Segoe UI", 10),
                                     selectmode='single', relief='flat', highlightthickness=0)
        modpack_listbox.pack(side='left', fill='both', expand=True)
        
        scrollbar = _tk.Scrollbar(listbox_frame, orient='vertical', command=modpack_listbox.yview)
        scrollbar.pack(side='right', fill='y')
        modpack_listbox.config(yscrollcommand=scrollbar.set)
        
        # Current modpack info
        info_frame = _tk.Frame(list_frame, bg='#1a1a1a')
        info_frame.grid(row=1, column=0, sticky='ew', padx=10, pady=(0, 10))
        
        info_label = _tk.Label(info_frame, text="No modpack selected", bg='#1a1a1a', fg='#CCCCCC',
                              font=("Segoe UI", 10))
        info_label.pack()
        
        # Buttons frame
        button_frame = _tk.Frame(dialog, bg='#1a1a1a')
        button_frame.pack(pady=(0, 20))
        
        def load_excel_file(file_path):
            try:
                configs = _EXCEL_MANAGER.load_from_excel(file_path)
                modpack_listbox.delete(0, _tk.END)
                for modpack_name in configs.keys():
                    modpack_listbox.insert(_tk.END, modpack_name)
                info_label.config(text=f"Loaded {len(configs)} modpack(s)")
            except Exception as e:
                _messagebox.showerror("Error", f"Failed to load Excel file:\n{e}")
        
        def save_excel_file():
            if _EXCEL_MANAGER.current_file:
                try:
                    _EXCEL_MANAGER.save_workbook(_EXCEL_MANAGER.current_file)
                    _messagebox.showinfo("Success", "Excel/CSV file saved successfully")
                except Exception as e:
                    _messagebox.showerror("Error", f"Failed to save Excel/CSV file:\n{e}")
            else:
                file_path = _filedialog.asksaveasfilename(
                    title="Save Excel/CSV File",
                    defaultextension=".csv" if _EXCEL_MANAGER.csv_mode else ".xlsx",
                    filetypes=[("Excel/CSV Files", "*.xlsx;*.csv"), ("Excel Files", "*.xlsx"), ("CSV Files", "*.csv"), ("All Files", "*.*")]
                )
                if file_path:
                    try:
                        _EXCEL_MANAGER.save_workbook(file_path)
                        excel_path_var.set(file_path)
                        _messagebox.showinfo("Success", "Excel/CSV file saved successfully")
                    except Exception as e:
                        _messagebox.showerror("Error", f"Failed to save Excel/CSV file:\n{e}")
        
        def edit_selected_modpack():
            selection = modpack_listbox.curselection()
            if not selection:
                _messagebox.showwarning("Warning", "Please select a modpack to edit")
                return
            
            modpack_name = modpack_listbox.get(selection[0])
            # Open edit dialog for selected modpack
            self._edit_modpack_dialog(dialog, modpack_name)
        
        def delete_selected_modpack():
            selection = modpack_listbox.curselection()
            if not selection:
                _messagebox.showwarning("Warning", "Please select a modpack to delete")
                return
            
            modpack_name = modpack_listbox.get(selection[0])
            if _messagebox.askyesno("Confirm", f"Delete modpack '{modpack_name}'?"):
                try:
                    sheet_name = _EXCEL_MANAGER._sanitize_sheet_name(modpack_name)
                    if sheet_name in _EXCEL_MANAGER.workbook.sheetnames:
                        _EXCEL_MANAGER.workbook.remove(_EXCEL_MANAGER.workbook[sheet_name])
                        modpack_listbox.delete(selection[0])
                        info_label.config(text=f"Deleted modpack '{modpack_name}'")
                except Exception as e:
                    _messagebox.showerror("Error", f"Failed to delete modpack:\n{e}")
        
        _tk.Button(button_frame, text="Load", command=lambda: load_excel_file(excel_path_var.get()), bg='#9333ea', fg='#FFFFFF',
                  font=("Segoe UI", 11), relief='flat', cursor='hand2', padx=15, pady=8).pack(side='left', padx=(0, 5))
        
        _tk.Button(button_frame, text="Save", command=save_excel_file, bg='#9333ea', fg='#FFFFFF',
                  font=("Segoe UI", 11), relief='flat', cursor='hand2', padx=15, pady=8).pack(side='left', padx=(0, 5))
        
        _tk.Button(button_frame, text="Edit", command=edit_selected_modpack, bg='#10b981', fg='#FFFFFF',
                  font=("Segoe UI", 11), relief='flat', cursor='hand2', padx=15, pady=8).pack(side='left', padx=(0, 5))
        
        _tk.Button(button_frame, text="Delete", command=delete_selected_modpack, bg='#ef4444', fg='#FFFFFF',
                  font=("Segoe UI", 11), relief='flat', cursor='hand2', padx=15, pady=8).pack(side='left', padx=(0, 5))
        
        def remerge_from_excel():
            selection = modpack_listbox.curselection()
            if not selection:
                _messagebox.showwarning("Warning", "Please select a modpack to re-merge")
                return
            
            modpack_name = modpack_listbox.get(selection[0])
            self._remerge_from_excel_dialog(dialog, modpack_name, excel_path_var.get())
        
        _tk.Button(button_frame, text="🔄 Re-merge", command=remerge_from_excel, bg='#f59e0b', fg='#FFFFFF',
                  font=("Segoe UI", 11), relief='flat', cursor='hand2', padx=15, pady=8).pack(side='left', padx=(0, 5))
        
        _tk.Button(button_frame, text="Close", command=dialog.destroy, bg='#1a1a1a', fg='#FFFFFF',
                  font=("Segoe UI", 11), relief='flat', cursor='hand2', padx=15, pady=8).pack(side='left')
