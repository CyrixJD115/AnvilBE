class AutoBEApp:
    
    def _create_modpack_organization_section(self):
        """Create the Modpack Organization section."""
        section_frame = _tk.Frame(self.help_content_frame, bg='#000000')
        
        org_card = _tk.LabelFrame(section_frame, text="📊 Modpack Organization", 
                                 bg='#1a1a1a', fg='#FFFFFF', font=("Segoe UI", 14, "bold"),
                                 relief='flat', bd=0)
        org_card.pack(fill='both', expand=True, padx=0, pady=(0, 15))
        
        org_inner = _tk.Frame(org_card, bg='#1a1a1a')
        org_inner.pack(fill='both', expand=True, padx=20, pady=15)
        
        # What is it
        what_card = _tk.Frame(org_inner, bg='#0A0A0A', relief='flat')
        what_card.pack(fill='x', pady=(0, 12), padx=5)
        _tk.Label(what_card, text="What is Modpack Organization?", bg='#0A0A0A', fg='#9333ea',
                  font=("Segoe UI", 11, "bold"), anchor='w').pack(fill='x', padx=12, pady=(12, 6))
        _tk.Label(what_card, 
                  text="Modpack Organization helps you track and manage the addons in your merged modpacks using Excel or CSV files. After merging, you can create a configuration file that lists all addons, their versions, and metadata.",
                  bg='#0A0A0A', fg='#CCCCCC', font=("Segoe UI", 10), anchor='w', justify='left', wraplength=650).pack(fill='x', padx=12, pady=(0, 12))
        
        # How to enable
        enable_card = _tk.Frame(org_inner, bg='#0A0A0A', relief='flat')
        enable_card.pack(fill='x', pady=(0, 12), padx=5)
        _tk.Label(enable_card, text="How to Enable", bg='#0A0A0A', fg='#9333ea',
                  font=("Segoe UI", 11, "bold"), anchor='w').pack(fill='x', padx=12, pady=(12, 6))
        enable_steps = [
            "• Go to the Settings tab",
            "• Find the 'Modpack Organization' section",
            "• Check 'Enable Excel/CSV organization'",
            "• Click 'Save Settings'",
        ]
        for step in enable_steps:
            _tk.Label(enable_card, text=step, bg='#0A0A0A', fg='#CCCCCC', font=("Segoe UI", 10),
                      anchor='w', justify='left', wraplength=650).pack(fill='x', padx=12, pady=(0, 4))
        _tk.Label(enable_card, text="Once enabled, the organization prompt will appear automatically after each merge.",
                  bg='#0A0A0A', fg='#9ca3af', font=("Segoe UI", 9), anchor='w', justify='left', wraplength=650).pack(fill='x', padx=12, pady=(8, 12))
        
        # Workflow
        workflow_card = _tk.Frame(org_inner, bg='#0A0A0A', relief='flat')
        workflow_card.pack(fill='x', pady=(0, 12), padx=5)
        _tk.Label(workflow_card, text="Complete Workflow", bg='#0A0A0A', fg='#9333ea',
                  font=("Segoe UI", 11, "bold"), anchor='w').pack(fill='x', padx=12, pady=(12, 6))
        workflow_steps = [
            "1. Select your .mcpack files in the main UI",
            "2. Click '🚀 Start Process' to merge",
            "3. After merge completes, a dialog appears asking for modpack name",
            "4. Enter modpack name, min/max versions, and click 'Create Excel/CSV'",
            "5. The system creates a configuration file in your output directory",
            "6. Open the file in Excel or any spreadsheet application to view/edit",
        ]
        for step in workflow_steps:
            _tk.Label(workflow_card, text=step, bg='#0A0A0A', fg='#CCCCCC', font=("Segoe UI", 10),
                      anchor='w', justify='left', wraplength=650).pack(fill='x', padx=12, pady=(0, 4))
        
        # Manual management
        manual_card = _tk.Frame(org_inner, bg='#0A0A0A', relief='flat')
        manual_card.pack(fill='x', pady=(0, 12), padx=5)
        _tk.Label(manual_card, text="Manual Management", bg='#0A0A0A', fg='#9333ea',
                  font=("Segoe UI", 11, "bold"), anchor='w').pack(fill='x', padx=12, pady=(12, 6))
        _tk.Label(manual_card, 
                  text="Click the '📊 Excel' button in the main UI to open the Excel/CSV Manager. From there you can:",
                  bg='#0A0A0A', fg='#CCCCCC', font=("Segoe UI", 10), anchor='w', justify='left', wraplength=650).pack(fill='x', padx=12, pady=(0, 6))
        manual_features = [
            "• Load existing Excel/CSV files",
            "• View all modpacks and their addons",
            "• Edit addon details (name, version, notes)",
            "• Delete addons from modpacks",
            "• Add new addons to modpacks",
            "• Save changes back to the file",
        ]
        for feature in manual_features:
            _tk.Label(manual_card, text=feature, bg='#0A0A0A', fg='#CCCCCC', font=("Segoe UI", 10),
                      anchor='w', justify='left', wraplength=650).pack(fill='x', padx=12, pady=(0, 4))
        
        # File format
        format_card = _tk.Frame(org_inner, bg='#0A0A0A', relief='flat')
        format_card.pack(fill='x', pady=(0, 12), padx=5)
        _tk.Label(format_card, text="File Format", bg='#0A0A0A', fg='#9333ea',
                  font=("Segoe UI", 11, "bold"), anchor='w').pack(fill='x', padx=12, pady=(12, 6))
        _tk.Label(format_card, 
                  text="The system automatically chooses the best format based on your system:",
                  bg='#0A0A0A', fg='#CCCCCC', font=("Segoe UI", 10), anchor='w', justify='left', wraplength=650).pack(fill='x', padx=12, pady=(0, 6))
        format_info = [
            "• CSV format (default): Works without any dependencies, can be opened in Excel",
            "• Excel format (.xlsx): Requires openpyxl library, provides richer formatting",
            "• Both formats contain the same data and can be used interchangeably",
        ]
        for info in format_info:
            _tk.Label(format_card, text=info, bg='#0A0A0A', fg='#CCCCCC', font=("Segoe UI", 10),
                      anchor='w', justify='left', wraplength=650).pack(fill='x', padx=12, pady=(0, 4))
        _tk.Label(format_card, text="No installation required - CSV mode works out of the box!",
                  bg='#0A0A0A', fg='#9ca3af', font=("Segoe UI", 9), anchor='w', justify='left', wraplength=650).pack(fill='x', padx=12, pady=(8, 12))
        
        # Future features
        future_card = _tk.Frame(org_inner, bg='#0A0A0A', relief='flat')
        future_card.pack(fill='x', pady=(0, 12), padx=5)
        _tk.Label(future_card, text="Coming Soon", bg='#0A0A0A', fg='#9333ea',
                  font=("Segoe UI", 11, "bold"), anchor='w').pack(fill='x', padx=12, pady=(12, 6))
        future_features = [
            "• Automatic modpack updates from Excel/CSV changes",
            "• Add new addons to existing modpacks without full re-merge",
            "• Update addon versions within modpacks",
            "• Remove addons from modpacks safely",
            "• Full integration with both merge modes (all together vs by script version)",
        ]
        for feature in future_features:
            _tk.Label(future_card, text=feature, bg='#0A0A0A', fg='#CCCCCC', font=("Segoe UI", 10),
                      anchor='w', justify='left', wraplength=650).pack(fill='x', padx=12, pady=(0, 4))
        
        return section_frame

    def check_manifest(self, file_path):
        """Check if the manifest.json exists in the mcpack/mcaddon file."""
        with _zipfile.ZipFile(file_path, 'r') as zip_ref:
            return 'manifest.json' in zip_ref.namelist()

    def sanitize_filename(self, filename):
        """Sanitize the filename to make it safe for the filesystem."""
        return _re.sub(r'[^\w\-_\. ]', '_', filename)

    def process_files(self, files, output_dir, save_each_pack_as_mcpack=False):
        """Process the selected .mcpack and .mcaddon files using recursive extraction, then merge/pack them. Optionally, save each found pack as a .mcpack in the output directory."""
        packs_to_process = []
        for input_file in files:
            ext = _os.path.splitext(input_file)[1].lower()
            if ext in ('.mcpack', '.mcaddon', '.zip'):
                packs = recursive_extract_pack(input_file)
                packs_to_process.extend(packs)
        # Optionally save each found pack as a .mcpack
        if save_each_pack_as_mcpack:
            for pack_folder in packs_to_process:
                out_name = _os.path.basename(pack_folder.rstrip('/\\')) + ".mcpack"
                out_path = _os.path.join(output_dir, out_name)
                folder_to_mcpack(pack_folder, out_path)
        # Now pass the valid pack folders to the main merge/pack logic
        if packs_to_process:
            self._process_packs(packs_to_process, output_dir)
        else:
            _messagebox.showerror(_("msg.error"), _("error.no_packs_found"))

    def _rebuild_mcpacker_file_list(self):
        for w in self._mcpacker_file_list_inner.winfo_children():
            w.destroy()
        self._mcpacker_file_list_photo_refs.clear()
        self._mcpacker_file_list_selected.clear()
        for idx, (display_name, path, photo, full_photo) in enumerate(self._mcpacker_file_list_data):
            row = _tk.Frame(self._mcpacker_file_list_inner, bg='#0A0A0A', height=52)
            row.pack(fill='x', padx=4, pady=2)
            row.pack_propagate(False)
            if photo:
                self._mcpacker_file_list_photo_refs.append(photo)
                if full_photo:
                    self._mcpacker_file_list_photo_refs.append(full_photo)
                icon_lbl = _tk.Label(row, image=photo, bg='#0A0A0A')
            else:
                icon_lbl = _tk.Label(row, text='\u26fa', font=('Segoe UI', 20), bg='#0A0A0A', fg='#666666')
            icon_lbl.pack(side=_tk.LEFT, padx=(8, 10), pady=6)
            name_lbl = _tk.Label(row, text=display_name, bg='#0A0A0A', fg='#FFFFFF', font=('Segoe UI', 10), anchor='w')
            name_lbl.pack(side=_tk.LEFT, fill='x', expand=True, pady=6)
            for c in (row, icon_lbl, name_lbl):
                c.bind('<Button-1>', lambda e, i=idx: self._toggle_mcpacker_file_selection(i))
                if hasattr(self, '_mcpacker_wheel_handler'):
                    for _ev in ('<MouseWheel>', '<Button-4>', '<Button-5>'):
                        c.bind(_ev, self._mcpacker_wheel_handler)
            row._idx = idx
        self._mcpacker_file_list_canvas.configure(scrollregion=self._mcpacker_file_list_canvas.bbox('all'))

    def _toggle_mcpacker_file_selection(self, idx):
        if idx in self._mcpacker_file_list_selected:
            self._mcpacker_file_list_selected.discard(idx)
        else:
            self._mcpacker_file_list_selected.add(idx)
        for row in self._mcpacker_file_list_inner.winfo_children():
            if hasattr(row, '_idx'):
                sel = row._idx in self._mcpacker_file_list_selected
                bg = '#9333ea' if sel else '#0A0A0A'
                row.config(bg=bg)
                for c in row.winfo_children():
                    c.config(bg=bg)

    def select_files(self):
        """Open file dialog to select .mcpack and .mcaddon files."""
        file_paths = _filedialog.askopenfilenames(
            title=_("filedialog.select_mcpack_mcaddon"),
            filetypes=[("Minecraft Files", "*.mcpack *.mcaddon")]
        )
        for file_path in file_paths:
            display_name, photo, full_photo = self._get_pack_display_info(file_path)
            self._mcpacker_file_list_data.append((display_name, file_path, photo, full_photo))
            self._mcpacker_file_paths[display_name] = file_path
        self._mcpacker_files = [item[1] for item in self._mcpacker_file_list_data]
        self._rebuild_mcpacker_file_list()
        self._update_mcpacker_file_count()

    def remove_mcpacker_files(self):
        for index in sorted(self._mcpacker_file_list_selected, reverse=True):
            if 0 <= index < len(self._mcpacker_file_list_data):
                self._mcpacker_file_list_data.pop(index)
        self._mcpacker_file_paths = {}
        for display_name, path, *_ in self._mcpacker_file_list_data:
            self._mcpacker_file_paths[display_name] = path
        self._mcpacker_files = list(self._mcpacker_file_paths.values())
        self._rebuild_mcpacker_file_list()
        self._update_mcpacker_file_count()

    def _toggle_select_all_mcpacker(self):
        """Select all MCPACKER files if not all selected, otherwise deselect all."""
        all_indices = set(range(len(self._mcpacker_file_list_data)))
        if self._mcpacker_file_list_selected >= all_indices:
            self._mcpacker_file_list_selected.clear()
            self._mcpacker_btn_select_all.config(text="Select All")
        else:
            self._mcpacker_file_list_selected = all_indices.copy()
            self._mcpacker_btn_select_all.config(text="Deselect All")
        for row in self._mcpacker_file_list_inner.winfo_children():
            if hasattr(row, '_idx'):
                sel = row._idx in self._mcpacker_file_list_selected
                bg = '#9333ea' if sel else '#1a1a1a'
                row.config(bg=bg)
                for c in row.winfo_children():
                    c.config(bg=bg)

    def _update_mcpacker_file_count(self):
        """Update the file count label for MCPACKER."""
        count = len(self._mcpacker_files)
        self._mcpacker_file_count_label.config(text=_f("app.files_selected", n=count))
        if hasattr(self, '_mcpacker_btn_select_all'):
            if count > 0:
                self._mcpacker_btn_select_all.grid()
                all_sel = self._mcpacker_file_list_selected >= set(range(count))
                self._mcpacker_btn_select_all.config(text="Deselect All" if all_sel else "Select All")
            else:
                self._mcpacker_btn_select_all.grid_remove()

    def _reset_mcpacker_list(self):
        """Clear MCPACKER file list and output selection (called from main thread) after process completes."""
        self._mcpacker_files = []
        self._mcpacker_file_paths = {}
        self._mcpacker_file_list_data = []
        self._mcpacker_file_list_selected.clear()
        self._mcpacker_file_list_photo_refs.clear()
        self.output_dir_var.set("")
        self._rebuild_mcpacker_file_list()
        self._update_mcpacker_file_count()

    def select_output_directory(self):
        """Open file dialog to select the output directory."""
        directory = _filedialog.askdirectory(title=_("filedialog.select_output_dir"))
        self.output_dir_var.set(directory)

    def start_process(self):
        """Start processing the selected files."""
        files = self.files_var.get().split(',')
        output_dir = self.output_dir_var.get()
        
        if not files or not output_dir:
            _messagebox.showerror(_("msg.error"), _("process.select_files_and_output"))
            return
        
        self.process_files(files, output_dir)
        _messagebox.showinfo(_("msg.success"), _("process.completed"))
        
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

    def _update_progress(self, step, progress_percent, message):
        """Update the progress display with current step and message."""
        if hasattr(self, '_progress_step_label'):
            self._progress_step_label.config(text=message)
            self._progress['value'] = progress_percent
            self._root.update_idletasks()
            
            # Update step indicators
            if hasattr(self, '_step_labels') and 1 <= step <= 4:
                for i in range(4):
                    if i < step - 1:
                        # Completed steps
                        self._step_labels[i]['status'].config(text="✓", fg='#9333ea')
                        self._step_labels[i]['label'].config(fg='#FFFFFF')
                    elif i == step - 1:
                        # Current step
                        self._step_labels[i]['status'].config(text="→", fg='#9333ea')
                        self._step_labels[i]['label'].config(fg='#9333ea')
                    else:
                        # Pending steps
                        self._step_labels[i]['status'].config(text="○", fg='#666666')
                        self._step_labels[i]['label'].config(fg='#999999')
                # Mark all as complete if step 4 is done
                if step == 4:
                    for i in range(4):
                        self._step_labels[i]['status'].config(text="✓", fg='#9333ea')
                        self._step_labels[i]['label'].config(fg='#FFFFFF')

    def _reset_progress(self):
        """Reset progress display to initial state."""
        if hasattr(self, '_progress_step_label'):
            self._progress_step_label.config(text=_("app.ready_to_process"))
            self._progress['value'] = 0
            if hasattr(self, '_step_labels'):
                for step_info in self._step_labels:
                    step_info['status'].config(text="○", fg='#666666')
                    step_info['label'].config(fg='#999999')

    def _show_subpack_selection(self, file_name, subpack_options):
        """Show a themed subpack selection overlay that matches the tool's theme."""
        # ── Palette ──────────────────────────────────────────────────────────
        C_OVERLAY   = '#080a0e'
        C_CARD      = '#111318'
        C_CARD_ALT  = '#1c2030'
        C_LIST_BG   = '#0b0d14'
        C_BORDER    = '#3a4260'
        C_ACCENT    = '#9333ea'
        C_ACCENT_LT = '#c084fc'
        C_ACCENT_DK = '#6b21a8'
        C_SEL_BG    = '#7c3aed'   # bright violet — clearly visible on selection
        C_SEL_FG    = '#ffffff'
        C_FG        = '#f0f4ff'   # near-white for max readability
        C_FG_MUTED  = '#8892a4'
        C_FG_DIM    = '#b0bcd4'
        C_NUM_BG    = '#231d3a'
        C_NUM_FG    = '#c4b5fd'

        # Clear existing widgets in overlay
        for widget in self._subpack_overlay.winfo_children():
            widget.destroy()
        self._subpack_overlay.configure(bg=C_OVERLAY)

        selection_done  = _tk.BooleanVar(self._root, False)
        selected_index  = [None]

        # ── Outer wrapper (dims background visually) ─────────────────────────
        center_frame = _tk.Frame(self._subpack_overlay, bg=C_OVERLAY)
        center_frame.place(relx=0.5, rely=0.5, anchor='center')

        # Accent glow border (1-px purple outline)
        glow = _tk.Frame(center_frame, bg=C_ACCENT, bd=0)
        glow.pack()

        # Card shell — sized by content; children use consistent padx to keep width stable
        card = _tk.Frame(glow, bg=C_CARD, bd=0)
        card.pack(padx=1, pady=1)

        # Top accent stripe
        _tk.Frame(card, bg=C_ACCENT, height=4).pack(fill='x')

        # ── Header ───────────────────────────────────────────────────────────
        hdr = _tk.Frame(card, bg=C_CARD)
        hdr.pack(fill='x', padx=28, pady=(18, 0))

        # Title row
        title_row = _tk.Frame(hdr, bg=C_CARD)
        title_row.pack(fill='x')
        _tk.Label(title_row, text='📦', bg=C_CARD, fg=C_ACCENT_LT,
                  font=('Segoe UI', 17)).pack(side='left', padx=(0, 8))
        _tk.Label(title_row, text=_("subpack.title"), bg=C_CARD, fg=C_FG,
                  font=('Segoe UI', 15, 'bold')).pack(side='left')

        # Count badge
        count_txt = f'{len(subpack_options)} variant{"s" if len(subpack_options) != 1 else ""}'
        badge = _tk.Label(title_row, text=count_txt, bg=C_NUM_BG, fg=C_NUM_FG,
                          font=('Segoe UI', 8, 'bold'), padx=8, pady=2)
        badge.pack(side='left', padx=(12, 0))

        # File name (truncated)
        _short = file_name if len(file_name) <= 56 else file_name[:53] + '…'
        _tk.Label(hdr, text=_short, bg=C_CARD, fg=C_FG_MUTED,
                  font=('Segoe UI', 9), anchor='w').pack(fill='x', pady=(5, 0))

        # ── Divider ───────────────────────────────────────────────────────────
        _tk.Frame(card, bg=C_BORDER, height=1).pack(fill='x', padx=28, pady=(14, 0))

        # ── Body ─────────────────────────────────────────────────────────────
        body = _tk.Frame(card, bg=C_CARD)
        body.pack(fill='both', expand=True, padx=28, pady=(14, 0))

        _tk.Label(body, text=_("subpack.instruction"),
                  bg=C_CARD, fg=C_FG_DIM, font=('Segoe UI', 9),
                  anchor='w').pack(fill='x', pady=(0, 8))

        # List border
        lb_border = _tk.Frame(body, bg=C_BORDER, bd=0)
        lb_border.pack(fill='both', expand=True, pady=(0, 14))

        lb_inner = _tk.Frame(lb_border, bg=C_LIST_BG, bd=0)
        lb_inner.pack(fill='both', expand=True, padx=1, pady=1)
        lb_inner.configure(height=260)
        lb_inner.pack_propagate(False)

        sb = _tk.Scrollbar(lb_inner, orient='vertical',
                           bg=C_CARD_ALT, troughcolor=C_LIST_BG,
                           activebackground=C_BORDER, width=13, relief='flat')
        sb.pack(side='right', fill='y')

        listbox = _tk.Listbox(lb_inner,
                              bg=C_LIST_BG, fg=C_FG,
                              font=('Segoe UI', 12),
                              selectbackground=C_SEL_BG,
                              selectforeground=C_SEL_FG,
                              relief='flat', bd=0,
                              yscrollcommand=sb.set,
                              highlightthickness=0,
                              activestyle='none',
                              cursor='hand2',
                              borderwidth=0,
                              selectborderwidth=0)
        listbox.pack(side='left', fill='both', expand=True)
        sb.config(command=listbox.yview)

        # Populate — number + spacing + name for clear readability
        for i, option in enumerate(subpack_options):
            listbox.insert(_tk.END, f'    {i + 1:>2}.   {option}')

        if subpack_options:
            listbox.selection_set(0)
            listbox.see(0)

        # Keyboard hint
        hint_row = _tk.Frame(body, bg=C_CARD)
        hint_row.pack(fill='x', pady=(0, 2))
        _tk.Label(hint_row, text='↵ Enter to confirm  ·  Esc to cancel  ·  Double-click to select',
                  bg=C_CARD, fg=C_FG_MUTED, font=('Segoe UI', 8),
                  anchor='w').pack(side='left')

        # ── Divider ───────────────────────────────────────────────────────────
        _tk.Frame(card, bg=C_BORDER, height=1).pack(fill='x', padx=28, pady=(8, 0))

        # ── Buttons ───────────────────────────────────────────────────────────
        btn_row = _tk.Frame(card, bg=C_CARD)
        btn_row.pack(fill='x', padx=28, pady=(14, 24))

        # Select (primary)
        ok_btn = _tk.Button(btn_row, text='  \u2714   ' + _("subpack.select") + '  ',
                            command=lambda: None,   # assigned below
                            bg=C_ACCENT, fg='#ffffff',
                            font=('Segoe UI', 11, 'bold'),
                            relief='flat', bd=0, cursor='hand2',
                            activebackground=C_ACCENT_LT,
                            activeforeground='#ffffff',
                            padx=8, pady=10)
        ok_btn.pack(side='right', padx=(10, 0))

        # Cancel (secondary)
        cancel_btn = _tk.Button(btn_row, text='  ' + _("common.cancel") + '  ',
                                command=lambda: None,
                                bg=C_CARD_ALT, fg=C_FG_DIM,
                                font=('Segoe UI', 11),
                                relief='flat', bd=0, cursor='hand2',
                                activebackground=C_BORDER,
                                activeforeground=C_FG,
                                padx=8, pady=10)
        cancel_btn.pack(side='right')

        # ── Actions ───────────────────────────────────────────────────────────
        def on_ok(_event=None):
            sel = listbox.curselection()
            if sel:
                selected_index[0] = sel[0] + 1
            selection_done.set(True)
            self._subpack_overlay.grid_remove()

        def on_cancel(_event=None):
            selected_index[0] = None
            selection_done.set(True)
            self._subpack_overlay.grid_remove()

        ok_btn.configure(command=on_ok)
        cancel_btn.configure(command=on_cancel)
        listbox.bind('<Double-Button-1>', on_ok)
        listbox.bind('<Return>', on_ok)
        card.bind_all('<Escape>', on_cancel)

        # ── Show ──────────────────────────────────────────────────────────────
        self._subpack_overlay.grid()
        self._subpack_overlay.tkraise()
        listbox.focus_set()
        self._root.update()

        self._root.wait_variable(selection_done)
        try:
            card.unbind_all('<Escape>')
        except Exception:
            pass
        
        return selected_index[0]

    def _rebuild_autobe_file_list(self):
        """Rebuild the AutoBE file list display (icon + name rows) from _file_list_data."""
        for w in self._file_list_inner.winfo_children():
            w.destroy()
        self._file_list_photo_refs.clear()
        self._file_list_selected.clear()
        for idx, (display_name, path, photo, full_photo) in enumerate(self._file_list_data):
            row = _tk.Frame(self._file_list_inner, bg='#0A0A0A', height=52)
            row.pack(fill='x', padx=4, pady=2)
            row.pack_propagate(False)
            if photo:
                self._file_list_photo_refs.append(photo)
                if full_photo:
                    self._file_list_photo_refs.append(full_photo)
                icon_lbl = _tk.Label(row, image=photo, bg='#0A0A0A')
            else:
                icon_lbl = _tk.Label(row, text='\u26fa', font=('Segoe UI', 20), bg='#0A0A0A', fg='#666666')
            icon_lbl.pack(side=_tk.LEFT, padx=(8, 10), pady=6)
            name_lbl = _tk.Label(row, text=display_name, bg='#0A0A0A', fg='#FFFFFF', font=('Segoe UI', 10), anchor='w')
            name_lbl.pack(side=_tk.LEFT, fill='x', expand=True, pady=6)
            for c in (row, icon_lbl, name_lbl):
                c.bind('<Button-1>', lambda e, i=idx: self._toggle_autobe_file_selection(i))
                if hasattr(self, '_file_list_wheel_handler'):
                    for _ev in ('<MouseWheel>', '<Button-4>', '<Button-5>'):
                        c.bind(_ev, self._file_list_wheel_handler)
            row._idx = idx
        self._file_list_canvas.configure(scrollregion=self._file_list_canvas.bbox('all'))

    def _toggle_autobe_file_selection(self, idx):
        if idx in self._file_list_selected:
            self._file_list_selected.discard(idx)
        else:
            self._file_list_selected.add(idx)
        for row in self._file_list_inner.winfo_children():
            if hasattr(row, '_idx'):
                sel = row._idx in self._file_list_selected
                bg = '#9333ea' if sel else '#0A0A0A'
                row.config(bg=bg)
                for c in row.winfo_children():
                    c.config(bg=bg)

    def _add_files(self):
        _files = _filedialog.askopenfilenames(filetypes=[("McPack files", "*.mcpack")])
        mcpack_names = []
        for _file in _files:
            display_name, photo, full_photo = self._get_pack_display_info(_file)
            self._file_list_data.append((display_name, _file, photo, full_photo))
            self._file_paths[display_name] = _file
            mcpack_names.append(_os.path.basename(_file))
        self._files = [item[1] for item in self._file_list_data]
        self.mcpack_names = mcpack_names
        self._rebuild_autobe_file_list()
        self._update_file_count()

    def _remove_files(self):
        for _index in sorted(self._file_list_selected, reverse=True):
            if 0 <= _index < len(self._file_list_data):
                self._file_list_data.pop(_index)
        self._file_paths = {}
        for display_name, path, *_ in self._file_list_data:
            self._file_paths[display_name] = path
        self._files = [item[1] for item in self._file_list_data]
        self._rebuild_autobe_file_list()
        self._update_file_count()

    def _toggle_select_all_files(self):
        """Select all files if not all selected, otherwise deselect all."""
        all_indices = set(range(len(self._file_list_data)))
        if self._file_list_selected >= all_indices:
            # All already selected -> deselect all
            self._file_list_selected.clear()
            self._btn_select_all.config(text="Select All")
        else:
            # Select all
            self._file_list_selected = all_indices.copy()
            self._btn_select_all.config(text="Deselect All")
        for row in self._file_list_inner.winfo_children():
            if hasattr(row, '_idx'):
                sel = row._idx in self._file_list_selected
                bg = '#9333ea' if sel else '#0A0A0A'
                row.config(bg=bg)
                for c in row.winfo_children():
                    c.config(bg=bg)

    def _update_file_count(self):
        """Update the file count label for AutoBE section."""
        count = len(self._files)
        self._file_count_label.config(text=_f("app.files_selected", n=count))
        # Show/hide Select All button depending on whether any files are loaded
        if hasattr(self, '_btn_select_all'):
            if count > 0:
                self._btn_select_all.grid()
                # Sync label with current selection state
                all_selected = self._file_list_selected >= set(range(count))
                self._btn_select_all.config(text="Deselect All" if all_selected else "Select All")
            else:
                self._btn_select_all.grid_remove()
        # Update achievement status when files change
        self._check_achievement_compatibility()

    def _check_achievement_compatibility(self):
        """Check if any packs disable achievements and update the status button."""
        if not hasattr(self, '_btn_achievement_status'):
            return
        
        self._achievement_disabling_packs = []
        
        # If no files selected, show default status
        if not self._files:
            self._btn_achievement_status.config(text="✅ " + _("app.achievements_active"), bg='#10b981', activebackground='#059669')
            return
        
        # Check each pack for achievement-disabling features (behavior packs only; RPs don't disable achievements)
        for _file in self._files:
            manifest_data = self._get_manifest_data(_file)
            if not manifest_data:
                continue
            
            # Resource packs never disable achievements; only check behavior packs
            modules = manifest_data.get('modules') or []
            if isinstance(modules, list) and len(modules) > 0:
                first_type = modules[0].get('type') if isinstance(modules[0], dict) else None
                if first_type == 'resources':
                    continue  # Skip RP; it does not disable achievements
            
            pack_name = _os.path.basename(_file)
            disables_achievements = False
            
            # Check for script_eval capability (most common cause)
            if 'capabilities' in manifest_data:
                capabilities = manifest_data['capabilities']
                if isinstance(capabilities, list):
                    if 'script_eval' in capabilities or 'experimental_custom_syntax' in capabilities:
                        disables_achievements = True
            
            # Check for script modules (type: "script")
            if 'modules' in manifest_data:
                modules = manifest_data['modules']
                if isinstance(modules, list):
                    for module in modules:
                        if isinstance(module, dict) and module.get('type') == 'script':
                            disables_achievements = True
                            break
            
            # Check for experimental gameplay features in header
            if 'header' in manifest_data:
                header = manifest_data['header']
                if isinstance(header, dict):
                    # Check for experimental field
                    if header.get('experimental') is True:
                        disables_achievements = True
            
            if disables_achievements:
                self._achievement_disabling_packs.append(pack_name)
        
        # Update button appearance only (no hover tooltip; click opens overlay)
        if self._achievement_disabling_packs:
            self._btn_achievement_status.config(text="❌ " + _("achievements.disabled"), bg='#ef4444', activebackground='#dc2626')
        else:
            self._btn_achievement_status.config(text="✅ " + _("app.achievements_active"), bg='#10b981', activebackground='#059669')

    def _show_achievement_overlay(self):
        """Show in-app screen with packs that disable achievements vs packs that do not. Same layout as Script API overlay."""
        for widget in self._achievement_overlay.winfo_children():
            widget.destroy()
        
        self._achievement_overlay.grid_columnconfigure(0, weight=1)
        self._achievement_overlay.grid_rowconfigure(0, weight=1)
        
        main_container = _tk.Frame(self._achievement_overlay, bg='#0f1419')
        main_container.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        main_container.grid_columnconfigure(0, weight=1)
        main_container.grid_rowconfigure(0, weight=1)
        
        card_frame = _tk.Frame(main_container, bg='#1a1a1a', relief='flat', bd=0)
        card_frame.grid(row=0, column=0, sticky="nsew")
        card_frame.grid_columnconfigure(0, weight=1)
        card_frame.grid_rowconfigure(1, weight=1)
        
        border_frame = _tk.Frame(card_frame, bg='#9333ea', height=3)
        border_frame.grid(row=0, column=0, sticky="ew")
        
        inner_frame = _tk.Frame(card_frame, bg='#1a1a1a')
        inner_frame.grid(row=1, column=0, sticky="nsew", padx=40, pady=30)
        inner_frame.grid_columnconfigure(0, weight=1)
        inner_frame.grid_rowconfigure(1, weight=1)
        
        title_label = _tk.Label(inner_frame, text="🏆 " + _("achievements.overlay_title"),
                               bg='#1a1a1a', fg='#FFFFFF', font=('Segoe UI', 18, 'bold'))
        title_label.grid(row=0, column=0, pady=(0, 6), sticky="w")
        
        if not self._files:
            msg_label = _tk.Label(inner_frame, text=_("achievements.no_packs_msg"),
                                 bg='#1a1a1a', fg='#999999', font=('Segoe UI', 11), wraplength=1200, justify='left')
            msg_label.grid(row=1, column=0, pady=20, sticky="w")
        else:
            disabling_set = set(self._achievement_disabling_packs)
            ok_packs = []
            for f in self._files:
                name = _os.path.basename(f)
                if name in disabling_set:
                    continue
                manifest_data = self._get_manifest_data(f)
                if not manifest_data:
                    continue
                modules = manifest_data.get('modules') or []
                if isinstance(modules, list) and len(modules) > 0:
                    first_type = modules[0].get('type') if isinstance(modules[0], dict) else None
                    if first_type == 'resources':
                        continue
                ok_packs.append(name)
            ok_packs = sorted(ok_packs)
            disabling_packs = sorted(self._achievement_disabling_packs)
            
            canvas_container = _tk.Frame(inner_frame, bg='#1a1a1a')
            canvas_container.grid(row=1, column=0, sticky="nsew")
            canvas_container.grid_columnconfigure(0, weight=1)
            canvas_container.grid_rowconfigure(0, weight=1)
            
            canvas = _tk.Canvas(canvas_container, bg='#1a1a1a', highlightthickness=0)
            scrollable_frame = _tk.Frame(canvas, bg='#1a1a1a')
            
            def update_scroll_region(event=None):
                canvas.update_idletasks()
                canvas.configure(scrollregion=canvas.bbox("all"))
            
            def _on_mousewheel(event):
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            
            def _scroll_bind_enter(event):
                canvas_container.bind_all("<MouseWheel>", _on_mousewheel)
            
            def _scroll_bind_leave(event):
                canvas_container.unbind_all("<MouseWheel>")
            
            scrollable_frame.bind("<Configure>", update_scroll_region)
            canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas.find_all()[0], width=e.width) if canvas.find_all() else None)
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas_container.bind("<Enter>", _scroll_bind_enter)
            canvas_container.bind("<Leave>", _scroll_bind_leave)
            canvas.bind("<Enter>", _scroll_bind_enter)
            scrollable_frame.bind("<Enter>", _scroll_bind_enter)
            
            row_num = 0
            
            dis_header = _tk.Frame(scrollable_frame, bg='#ef4444', height=42)
            dis_header.grid(row=row_num, column=0, sticky="ew", padx=0, pady=(0, 0))
            dis_header.grid_columnconfigure(0, weight=1)
            d_count = len(disabling_packs)
            _tk.Label(dis_header, text=f"  ❌ Packs that DISABLE achievements  ·  {d_count} pack{'s' if d_count != 1 else ''}  ",
                     bg='#ef4444', fg='#FFFFFF', font=('Segoe UI', 12, 'bold'), anchor='w').grid(row=0, column=0, padx=20, pady=10, sticky="w")
            row_num += 1
            for pack_name in disabling_packs:
                display_name = (pack_name[:80] + "…") if len(pack_name) > 80 else pack_name
                row_f = _tk.Frame(scrollable_frame, bg='#1a1a1a', height=36)
                row_f.grid(row=row_num, column=0, sticky="ew", padx=20, pady=2)
                row_f.grid_columnconfigure(0, weight=1)
                _tk.Label(row_f, text=display_name, bg='#1a1a1a', fg='#fca5a5', font=('Segoe UI', 11), anchor='w').grid(row=0, column=0, padx=24, pady=8, sticky="w")
                row_num += 1
            row_num += 6
            
            ok_header = _tk.Frame(scrollable_frame, bg='#10b981', height=42)
            ok_header.grid(row=row_num, column=0, sticky="ew", padx=0, pady=(0, 0))
            ok_header.grid_columnconfigure(0, weight=1)
            o_count = len(ok_packs)
            _tk.Label(ok_header, text=f"  ✅ Packs that do NOT disable achievements  ·  {o_count} pack{'s' if o_count != 1 else ''}  ",
                     bg='#10b981', fg='#FFFFFF', font=('Segoe UI', 12, 'bold'), anchor='w').grid(row=0, column=0, padx=20, pady=10, sticky="w")
            row_num += 1
            for pack_name in ok_packs:
                display_name = (pack_name[:80] + "…") if len(pack_name) > 80 else pack_name
                row_f = _tk.Frame(scrollable_frame, bg='#1a1a1a', height=36)
                row_f.grid(row=row_num, column=0, sticky="ew", padx=20, pady=2)
                row_f.grid_columnconfigure(0, weight=1)
                _tk.Label(row_f, text=display_name, bg='#1a1a1a', fg='#6ee7b7', font=('Segoe UI', 11), anchor='w').grid(row=0, column=0, padx=24, pady=8, sticky="w")
                row_num += 1
            
            scrollable_frame.grid_columnconfigure(0, weight=1)
            canvas.grid(row=0, column=0, sticky="nsew")
            self._root.after(100, update_scroll_region)
        
        def on_close():
            self._achievement_overlay.grid_remove()
        
        button_frame = _tk.Frame(inner_frame, bg='#1a1a1a')
        button_frame.grid(row=2, column=0, pady=(15, 0))
        close_btn = _tk.Button(button_frame, text=_("common.close"), command=on_close,
                              bg='#9333ea', fg='#FFFFFF', font=('Segoe UI', 11, 'bold'),
                              relief='flat', cursor='hand2', activebackground='#a855f7',
                              padx=30, pady=10)
        close_btn.pack()
        
        self._achievement_overlay.grid()
        self._achievement_overlay.lift()

    def _detect_com_mojang(self):
        """Return the first existing com.mojang path from known locations."""
        candidates = [
            _os.path.join(_os.environ.get('APPDATA', ''), 'Minecraft Bedrock', 'Users', 'Shared', 'games', 'com.mojang'),
            _os.path.expandvars(r'%LOCALAPPDATA%\Packages\Microsoft.MinecraftUWP_8wekyb3d8bbwe\LocalState\games\com.mojang'),
            _os.path.expandvars(r'%LOCALAPPDATA%\Packages\Microsoft.MinecraftWindowsBeta_8wekyb3d8bbwe\LocalState\games\com.mojang'),
        ]
        for c in candidates:
            if _os.path.isdir(c):
                return c
        return ''

    def _toggle_mc_import_path(self):
        """Enable or disable the com.mojang path entry based on the checkbox state."""
        enabled = self._auto_import_var.get()
        state = 'normal' if enabled else 'disabled'
        fg_entry = '#FFFFFF' if enabled else '#888888'
        fg_btn   = '#FFFFFF' if enabled else '#888888'
        bg_btn   = '#9333ea' if enabled else '#374151'
        try:
            entry = getattr(self, '_entry_mc_path', None)
            if entry and entry.winfo_exists():
                entry.config(state=state, fg=fg_entry)
        except Exception:
            pass
        try:
            btn = getattr(self, '_btn_mc_browse', None)
            if btn and btn.winfo_exists():
                btn.config(state=state, fg=fg_btn, bg=bg_btn)
        except Exception:
            pass

    def _browse_mc_path(self):
        """Let the user browse to a custom com.mojang directory."""
        path = _filedialog.askdirectory(title="Select com.mojang folder")
        if path:
            self._mc_path_var.set(path)

    def _import_to_minecraft(self, base_dir):
        """Unzip the merged behavior_pack.mcpack / resource_pack.mcpack into com.mojang."""
        mc_path = self._mc_path_var.get().strip()
        if not mc_path or not _os.path.isdir(mc_path):
            _logging.warning(f"Auto-import skipped — com.mojang path not found: {mc_path!r}")
            self._root.after(0, lambda p=mc_path: self._show_import_panel([], error=f"com.mojang folder not found:\n{p}"))
            return
        bp_dest_root = _os.path.join(mc_path, 'behavior_packs')
        rp_dest_root = _os.path.join(mc_path, 'resource_packs')
        _os.makedirs(bp_dest_root, exist_ok=True)
        _os.makedirs(rp_dest_root, exist_ok=True)
        imported = []
        # Collect all output dirs (base_dir itself + version subdirs)
        dirs_to_check = [base_dir] + [_os.path.join(base_dir, d) for d in _os.listdir(base_dir)
                                      if _os.path.isdir(_os.path.join(base_dir, d))]
        for out_dir in dirs_to_check:
            tag = _os.path.basename(out_dir) if out_dir != base_dir else 'merged'
            pack_name = f'AutoBE_{tag}'
            for mcpack, dest_root, kind in [
                ('behavior_pack.mcpack',  bp_dest_root, 'BP'),
                ('resource_pack.mcpack',  rp_dest_root, 'RP'),
            ]:
                src = _os.path.join(out_dir, mcpack)
                if not _os.path.isfile(src):
                    continue
                dest = _os.path.join(dest_root, f'{pack_name}_{kind}')
                if _os.path.isdir(dest):
                    _shutil.rmtree(dest)
                _os.makedirs(dest, exist_ok=True)
                try:
                    with _zipfile.ZipFile(src, 'r') as _z:
                        _z.extractall(dest)
                    imported.append(f'{pack_name}_{kind}')
                    _logging.info(f"Auto-imported {mcpack} → {dest}")
                except Exception as _e:
                    _logging.error(f"Auto-import failed for {src}: {_e}")
        if imported:
            self._root.after(0, lambda i=imported: self._show_import_panel(i))
        else:
            _logging.warning("Auto-import: no merged packs found to import.")
