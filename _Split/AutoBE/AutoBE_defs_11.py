class AutoBEApp:
    
    def _edit_modpack_dialog(self, parent_dialog, modpack_name):
        """Open dialog to edit a specific modpack's addons."""
        sheet_name = _EXCEL_MANAGER._sanitize_sheet_name(modpack_name)
        if sheet_name not in _EXCEL_MANAGER.workbook.sheetnames:
            _messagebox.showerror("Error", f"Modpack '{modpack_name}' not found")
            return
        
        sheet = _EXCEL_MANAGER.workbook[sheet_name]
        modpack_config = _EXCEL_MANAGER._parse_modpack_sheet(sheet)
        
        dialog = _tk.Toplevel(parent_dialog)
        dialog.title(f"Edit {modpack_name}")
        dialog.geometry("800x500")
        dialog.configure(bg='#1a1a1a')
        dialog.transient(parent_dialog)
        dialog.grab_set()
        
        # Title
        _tk.Label(dialog, text=f"📦 {modpack_name}", bg='#1a1a1a', fg='#FFFFFF',
                 font=("Segoe UI", 14, "bold")).pack(pady=(15, 10))
        
        # Addon list frame
        list_frame = _tk.LabelFrame(dialog, text="Addons", bg='#1a1a1a', fg='#FFFFFF',
                                    font=("Segoe UI", 11, "bold"))
        list_frame.pack(fill='both', expand=True, padx=15, pady=(0, 10))
        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(0, weight=1)
        
        # Treeview for addon list
        from tkinter import ttk
        tree_frame = _tk.Frame(list_frame, bg='#1a1a1a')
        tree_frame.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)
        
        columns = ("name", "version", "min_version", "max_version", "status")
        tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=15)
        tree.heading("name", text="Addon Name")
        tree.heading("version", text="Version")
        tree.heading("min_version", text="Min Ver")
        tree.heading("max_version", text="Max Ver")
        tree.heading("status", text="Status")
        
        tree.column("name", width=200)
        tree.column("version", width=100)
        tree.column("min_version", width=80)
        tree.column("max_version", width=80)
        tree.column("status", width=80)
        
        tree.pack(side='left', fill='both', expand=True)
        
        # Scrollbar
        tree_scroll = _tk.Scrollbar(tree_frame, orient='vertical', command=tree.yview)
        tree_scroll.pack(side='right', fill='y')
        tree.config(yscrollcommand=tree_scroll.set)
        
        # Populate tree
        for addon in modpack_config["addons"]:
            tree.insert('', 'end', values=(
                addon["name"],
                addon["version"],
                addon["min_version"],
                addon["max_version"],
                addon["status"]
            ))
        
        # Buttons
        button_frame = _tk.Frame(dialog, bg='#1a1a1a')
        button_frame.pack(pady=(0, 15))
        
        def add_addon():
            # Simple dialog to add addon
            add_dialog = _tk.Toplevel(dialog)
            add_dialog.title("Add Addon")
            add_dialog.geometry("400x300")
            add_dialog.configure(bg='#1a1a1a')
            add_dialog.transient(dialog)
            add_dialog.grab_set()
            
            _tk.Label(add_dialog, text="Addon Name:", bg='#1a1a1a', fg='#FFFFFF',
                     font=("Segoe UI", 10)).pack(pady=(10, 5))
            name_var = _tk.StringVar()
            _tk.Entry(add_dialog, textvariable=name_var, width=40, bg='#0A0A0A', fg='#FFFFFF').pack(pady=5)
            
            _tk.Label(add_dialog, text="Version:", bg='#1a1a1a', fg='#FFFFFF',
                     font=("Segoe UI", 10)).pack(pady=(10, 5))
            version_var = _tk.StringVar(value="1.0.0")
            _tk.Entry(add_dialog, textvariable=version_var, width=40, bg='#0A0A0A', fg='#FFFFFF').pack(pady=5)
            
            def confirm_add():
                new_addon = {
                    "name": name_var.get(),
                    "path": "",
                    "version": version_var.get(),
                    "min_version": modpack_config.get("min_version", "1.21.0"),
                    "max_version": modpack_config.get("max_version", "1.21.90"),
                    "status": "Active",
                    "notes": ""
                }
                modpack_config["addons"].append(new_addon)
                tree.insert('', 'end', values=(new_addon["name"], new_addon["version"], 
                                                new_addon["min_version"], new_addon["max_version"], new_addon["status"]))
                add_dialog.destroy()
            
            _tk.Button(add_dialog, text="Add", command=confirm_add, bg='#9333ea', fg='#FFFFFF',
                      font=("Segoe UI", 10), relief='flat').pack(pady=10)
        
        def remove_addon():
            selection = tree.selection()
            if not selection:
                _messagebox.showwarning("Warning", "Please select an addon to remove")
                return
            if _messagebox.askyesno("Confirm", "Remove selected addon?"):
                item = tree.selection()[0]
                index = tree.index(item)
                del modpack_config["addons"][index]
                tree.delete(item)
        
        def save_changes():
            # Update the sheet with new data
            _EXCEL_MANAGER.workbook.remove(sheet)
            _EXCEL_MANAGER.add_modpack_sheet(
                modpack_name,
                modpack_config["addons"],
                min_version=modpack_config.get("min_version", "1.21.0"),
                max_version=modpack_config.get("max_version", "1.21.90")
            )
            _messagebox.showinfo("Success", "Changes saved to workbook")
            dialog.destroy()
        
        _tk.Button(button_frame, text="Add Addon", command=add_addon, bg='#10b981', fg='#FFFFFF',
                  font=("Segoe UI", 10), relief='flat', cursor='hand2', padx=12, pady=6).pack(side='left', padx=(0, 5))
        
        _tk.Button(button_frame, text="Remove", command=remove_addon, bg='#ef4444', fg='#FFFFFF',
                  font=("Segoe UI", 10), relief='flat', cursor='hand2', padx=12, pady=6).pack(side='left', padx=(0, 5))
        
        _tk.Button(button_frame, text="Save Changes", command=save_changes, bg='#9333ea', fg='#FFFFFF',
                  font=("Segoe UI", 10), relief='flat', cursor='hand2', padx=12, pady=6).pack(side='left', padx=(0, 5))
        
        _tk.Button(button_frame, text="Close", command=dialog.destroy, bg='#1a1a1a', fg='#FFFFFF',
                  font=("Segoe UI", 10), relief='flat', cursor='hand2', padx=12, pady=6).pack(side='left')
    
    def _remerge_from_excel_dialog(self, parent_dialog, modpack_name, excel_path):
        """Dialog to confirm and execute re-merge from Excel/CSV file."""
        if not excel_path or not _os.path.isfile(excel_path):
            _messagebox.showerror("Error", "Please load an Excel/CSV file first")
            return
        
        try:
            configs = _EXCEL_MANAGER.load_from_excel(excel_path)
            if modpack_name not in configs:
                _messagebox.showerror("Error", f"Modpack '{modpack_name}' not found in Excel/CSV file")
                return
            
            modpack_config = configs[modpack_name]
            addons = modpack_config.get("addons", [])
            
            if not addons:
                _messagebox.showerror("Error", f"No addons found in modpack '{modpack_name}'")
                return
            
            # Check if all file paths exist
            missing_files = []
            valid_files = []
            for addon in addons:
                path = addon.get("path", "")
                if not path or not _os.path.isfile(path):
                    missing_files.append(addon.get("name", "Unknown"))
                else:
                    valid_files.append(path)
            
            if missing_files:
                _messagebox.showwarning("Missing Files", 
                    f"The following addon files are missing:\n" + "\n".join(missing_files) + 
                    f"\n\nOnly {len(valid_files)} valid files will be merged.")
            
            if not valid_files:
                _messagebox.showerror("Error", "No valid addon files found to merge")
                return
            
            # Confirm dialog
            confirm_dialog = _tk.Toplevel(parent_dialog)
            confirm_dialog.title("Confirm Re-merge")
            confirm_dialog.configure(bg='#1a1a1a')
            confirm_dialog.transient(parent_dialog)
            confirm_dialog.grab_set()
            
            # Main container with padding
            main_frame = _tk.Frame(confirm_dialog, bg='#1a1a1a')
            main_frame.pack(fill='both', expand=True, padx=30, pady=30)
            
            _tk.Label(main_frame, text="🔄 Re-merge Modpack", bg='#1a1a1a', fg='#FFFFFF',
                     font=("Segoe UI", 16, "bold")).pack(pady=(0, 15))
            
            _tk.Label(main_frame, text=f"Modpack: {modpack_name}", bg='#1a1a1a', fg='#CCCCCC',
                     font=("Segoe UI", 11)).pack(pady=(0, 10))
            
            _tk.Label(main_frame, text=f"Addons to merge: {len(valid_files)}", bg='#1a1a1a', fg='#CCCCCC',
                     font=("Segoe UI", 11)).pack(pady=(0, 10))
            
            if missing_files:
                _tk.Label(main_frame, text=f"⚠️ {len(missing_files)} files missing (will be skipped)", bg='#1a1a1a', fg='#f59e0b',
                         font=("Segoe UI", 10)).pack(pady=(0, 20))
            else:
                _tk.Label(main_frame, text="All addon files found ✓", bg='#1a1a1a', fg='#10b981',
                         font=("Segoe UI", 10)).pack(pady=(0, 20))
            
            # Output directory selection
            _tk.Label(main_frame, text="Output Directory:", bg='#1a1a1a', fg='#FFFFFF',
                     font=("Segoe UI", 11)).pack(pady=(0, 5), anchor='w')
            
            output_dir_var = _tk.StringVar(value=self._output_dir_var.get())
            output_entry = _tk.Entry(main_frame, textvariable=output_dir_var, width=50, bg='#0A0A0A', fg='#FFFFFF',
                                   font=("Segoe UI", 10), relief='flat')
            output_entry.pack(pady=(0, 20), fill='x')
            
            def browse_output():
                dir_path = _filedialog.askdirectory(title="Select Output Directory")
                if dir_path:
                    output_dir_var.set(dir_path)
            
            _tk.Button(main_frame, text="Browse", command=browse_output, bg='#9333ea', fg='#FFFFFF',
                     font=("Segoe UI", 10), relief='flat', cursor='hand2').pack(pady=(0, 20))
            
            def confirm_remerge():
                output_dir = output_dir_var.get()
                if not output_dir:
                    _messagebox.showerror("Error", "Please select an output directory")
                    return
                
                try:
                    # Close the Excel manager dialog
                    parent_dialog.destroy()
                    confirm_dialog.destroy()
                    
                    # Load files into the main UI
                    self._files = valid_files
                    self._file_paths = {_os.path.basename(f): f for f in valid_files}
                    self._file_list_data = []
                    for file_path in valid_files:
                        display_name, photo, full_photo = self._get_pack_display_info(file_path)
                        self._file_list_data.append((display_name, file_path, photo, full_photo))
                    
                    # Update the file list UI
                    self._rebuild_autobe_file_list()
                    self._update_file_count()
                    
                    # Set output directory
                    self._output_dir_var.set(output_dir)
                    
                    # Start the merge process
                    self._start_process()
                    
                except Exception as e:
                    _logging.error(f"Error during re-merge: {e}")
                    _messagebox.showerror("Error", f"Failed to start re-merge:\n{e}")
            
            def cancel():
                confirm_dialog.destroy()
            
            button_frame = _tk.Frame(main_frame, bg='#1a1a1a')
            button_frame.pack(pady=(10, 0))
            
            _tk.Button(button_frame, text="🔄 Start Re-merge", command=confirm_remerge, bg='#9333ea', fg='#FFFFFF',
                     font=("Segoe UI", 11, "bold"), relief='flat', cursor='hand2', padx=20, pady=8).pack(side='left', padx=(0, 10))
            
            _tk.Button(button_frame, text="Cancel", command=cancel, bg='#1a1a1a', fg='#FFFFFF',
                     font=("Segoe UI", 11), relief='flat', cursor='hand2', padx=20, pady=8).pack(side='left')
            
            # Center dialog
            confirm_dialog.update_idletasks()
            width = confirm_dialog.winfo_reqwidth()
            height = confirm_dialog.winfo_reqheight()
            x = (confirm_dialog.winfo_screenwidth() // 2) - (width // 2)
            y = (confirm_dialog.winfo_screenheight() // 2) - (height // 2)
            confirm_dialog.geometry(f"{width}x{height}+{x}+{y}")
            confirm_dialog.minsize(width, height)
            
        except Exception as e:
            _logging.error(f"Error loading Excel/CSV for re-merge: {e}")
            _messagebox.showerror("Error", f"Failed to load Excel/CSV file:\n{e}")
    
    def _reset_file_list(self):
        """Reset file list and output selection (called from main thread) after process completes."""
        self._files = []
        self._file_paths = {}
        self._file_list_data = []
        self._output_dir_var.set("")
        self._rebuild_autobe_file_list()
        self._update_file_count()

    def _start_process(self):
        """
        Starts the processing of selected .mcpack files and saves the output to the specified directory.
        """
        # Use full file paths from _files list (listbox now only shows filenames)
        _selected_files = self._files
        # When merge-by-script-version is used, self._out_dir is set to the version subfolder; use it so each group writes to its own folder
        _output_dir = (getattr(self, "_out_dir", None) or "").strip() or self._output_dir_var.get()

        if not _selected_files:
            self._root.after(0, lambda: _messagebox.showerror(_("msg.error"), _("process.select_at_least_one")))
            return
        if not _output_dir:
            self._root.after(0, lambda: _messagebox.showerror(_("msg.error"), _("process.select_output")))
            return

        # Sweep source directories for any _modified.mcpack files left over from a
        # previously interrupted merge and delete them before starting a fresh one.
        _source_dirs = {_os.path.dirname(f) for f in _selected_files if f}
        for _src_dir in _source_dirs:
            try:
                for _leftover in _os.listdir(_src_dir):
                    if _leftover.endswith('_modified.mcpack'):
                        try:
                            _os.remove(_os.path.join(_src_dir, _leftover))
                        except Exception:
                            pass
            except Exception:
                pass

        # Mark merge as active so Discord idle refresh doesn't override merge-specific status
        self._discord_merging = True
        self._merge_discord_start = int(_datetime.datetime.now().timestamp())
        self._discord_merge_last_update = 0
        self._set_discord_merge_step("Starting merge...", f"Loading {len(_selected_files)} addons")

        new_selected_files = []  # Stores all files to be processed (modified and unmodified)
        new_mcpack_paths = []    # Stores paths of modified files for cleanup later
        self._pending_cleanup_mcpacks = new_mcpack_paths  # expose to thread finally for guaranteed cleanup

        for file_path in _selected_files:
            try:
                # Already-processed modified copies — skip the subpack dialog entirely
                if file_path.lower().endswith('_modified.mcpack'):
                    new_selected_files.append(file_path)
                    continue

                # Use the improved _get_manifest_data method which handles comments and malformed JSON
                manifest_data = self._get_manifest_data(file_path)
                if manifest_data is None:
                    _messagebox.showerror(_("msg.error"), _f("process.no_manifest_in_file", path=file_path))
                    continue

                # Check if 'subpacks' exists in manifest
                if 'subpacks' not in manifest_data:
                    # No subpacks found, add the original file to the list
                    new_selected_files.append(file_path)
                    continue

                subpacks = manifest_data['subpacks']
                if not subpacks:
                    # No subpacks defined, add the original file to the list
                    new_selected_files.append(file_path)
                    continue

                # Prepare subpack options for the user
                subpack_options = []
                for subpack in subpacks:
                    folder_name = subpack.get('folder_name', '')
                    name = subpack.get('name', '')
                    if folder_name and name:
                        subpack_options.append(f"{name} (Folder: {folder_name})")

                if not subpack_options:
                    new_selected_files.append(file_path)
                    continue

                # Prompt the user to select a subpack using themed dialog
                file_name_display = _os.path.basename(file_path)
                _sp_short = file_name_display if len(file_name_display) <= 40 else file_name_display[:37] + "..."
                self._set_discord_merge_step("Selecting subpack", _sp_short)
                # Must call from main thread for dialog
                if threading.current_thread() is threading.main_thread():
                    selected_subpack_index = self._show_subpack_selection(file_name_display, subpack_options)
                else:
                    # If in background thread, we need to call on main thread and wait
                    selected_index_var = [None]
                    event = threading.Event()
                    
                    def show_dialog():
                        try:
                            selected_index_var[0] = self._show_subpack_selection(file_name_display, subpack_options)
                        finally:
                            event.set()
                    
                    self._root.after(0, show_dialog)
                    event.wait()  # Wait for dialog to complete
                    selected_subpack_index = selected_index_var[0]

                if selected_subpack_index is None:
                    continue

                selected_subpack = subpacks[selected_subpack_index - 1]
                selected_subpack_name = selected_subpack['folder_name']

                # Create temporary directory
                temp_dir = _tempfile.mkdtemp(prefix='temp_extract_')
                # Extract the selected subpack folder
                with _zipfile.ZipFile(file_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)

                subpack_path = _os.path.join(temp_dir, 'subpacks', selected_subpack_name)

                # Check if subpack_path exists
                if not _os.path.exists(subpack_path):
                    new_selected_files.append(file_path)
                    continue

                # Move the contents of the selected folder outside the 'subpacks' folder
                for item in _os.listdir(subpack_path):
                    s = _os.path.join(subpack_path, item)
                    d = _os.path.join(temp_dir, item)
                    if _os.path.exists(d):
                        if _os.path.isdir(d):
                            _shutil.copytree(s, d, dirs_exist_ok=True)
                        else:
                            _shutil.move(s, d)
                    else:
                        _shutil.move(s, d)

                # Remove the now empty 'subpacks' folder
                subpacks_dir = _os.path.join(temp_dir, 'subpacks')
                if _os.path.exists(subpacks_dir):
                    _shutil.rmtree(subpacks_dir)

                # Repack the .mcpack file — strip 'subpacks' from manifest so
                # the modified copy never triggers the subpack dialog again
                new_mcpack_path = file_path.replace('.mcpack', '_modified.mcpack')
                with _zipfile.ZipFile(new_mcpack_path, 'w') as new_zip_ref:
                    for folder_name, subfolders, filenames in _os.walk(temp_dir):
                        for filename in filenames:
                            file_path_in_temp = _os.path.join(folder_name, filename)
                            arcname = _os.path.relpath(file_path_in_temp, temp_dir)
                            if filename.lower() == 'manifest.json' and arcname.lower() == 'manifest.json':
                                try:
                                    with open(file_path_in_temp, 'r', encoding='utf-8') as _mf:
                                        _mdata = _json.load(_mf)
                                    _mdata.pop('subpacks', None)
                                    new_zip_ref.writestr(arcname, _json.dumps(_mdata, indent=2))
                                    continue
                                except Exception:
                                    pass
                            new_zip_ref.write(file_path_in_temp, arcname)

                # Clean up the temporary directory
                if _os.path.exists(temp_dir):
                    _shutil.rmtree(temp_dir)

                # Add the new modified file to the list
                new_selected_files.append(new_mcpack_path)
                new_mcpack_paths.append(new_mcpack_path)

            except Exception as e:
                log_error(e)
                _messagebox.showerror(_("msg.error"), _f("process.error_processing_file", path=file_path, error=str(e)))
                continue

        if not new_selected_files:
            _messagebox.showerror(_("msg.error"), _("process.no_valid_mcpacks"))
            return

        try:
            _logging.info("Step: _extract_and_store_highest_versions")
            self._extract_and_store_highest_versions()
        except Exception as e:
            _logging.error("_extract_and_store_highest_versions failed", exc_info=True)

        try:
            _logging.info(f"Step: _process_packs ({len(new_selected_files)} files) -> {_output_dir}")
            self._process_packs(new_selected_files, _output_dir)
            _logging.info("Step: _process_packs complete")
        except Exception as e:
            _logging.error("_process_packs failed", exc_info=True)

        try:
            _logging.info("Step: _delete_manifest_files")
            self._delete_manifest_files()
        except Exception as e:
            _logging.error("_delete_manifest_files failed", exc_info=True)

        # Pre-merge: scan scripts for runtime property write conflicts and warn user
        try:
            self._update_progress(1, 2, "Pre-check: Scanning scripts for runtime conflicts...")
            _script_conflicts = self._scan_script_runtime_conflicts(new_selected_files)
            if _script_conflicts:
                _conflict_lines = ["The following packs write to the same entity/world properties at runtime.",
                                   "The LAST pack listed for each conflict will win — others may be partially overridden.",
                                   "You can still merge; this is a warning only.\n"]
                for (_comp, _prop), _pack_hits in sorted(_script_conflicts.items()):
                    if len(_pack_hits) > 1:
                        _conflict_lines.append(f"  {_comp}.{_prop}:")
                        for _pname, _file, _lineno in _pack_hits:
                            _conflict_lines.append(f"    → {_pname}  ({_file}:{_lineno})")
                _conflict_text = "\n".join(_conflict_lines)
                _done = threading.Event()
                def _show_warn():
                    try:
                        _win = _tk.Toplevel(self._root)
                        _win.title("Script Runtime Conflict Report")
                        _win.configure(bg='#1a1a2e')
                        _win.resizable(True, True)
                        _win.geometry("800x600")
                        _win.minsize(600, 400)
                        _win.grab_set()
                        
                        # Main container with padding
                        _container = _tk.Frame(_win, bg='#1a1a2e')
                        _container.pack(fill='both', expand=True, padx=32, pady=32)
                        
                        # Header
                        _tk.Label(_container, text="⚠ Script Runtime Conflict Report",
                                  bg='#1a1a2e', fg='#f97316',
                                  font=("Segoe UI", 14, "bold")).pack(pady=(0, 8))
                        
                        # Subtitle
                        _tk.Label(_container, text="These conflicts cannot be auto-fixed — both scripts run, last write wins.",
                                  bg='#1a1a2e', fg='#cbd5e1',
                                  font=("Segoe UI", 10)).pack(pady=(0, 16))
                        
                        # Text frame with border
                        _txt_frame = _tk.Frame(_container, bg='#16213e', relief='solid', borderwidth=1)
                        _txt_frame.pack(fill='both', expand=True, pady=(0, 20))
                        
                        _inner_frame = _tk.Frame(_txt_frame, bg='#16213e')
                        _inner_frame.pack(fill='both', expand=True, padx=1, pady=1)
                        
                        _sb = _tk.Scrollbar(_inner_frame)
                        _sb.pack(side='right', fill='y')
                        
                        _txt = _tk.Text(_inner_frame, bg='#16213e', fg='#e2e8f0', font=("Consolas", 9),
                                        wrap='word', yscrollcommand=_sb.set, relief='flat', padx=12, pady=12)
                        _txt.pack(fill='both', expand=True, side='left')
                        _sb.config(command=_txt.yview)
                        
                        _txt.insert('1.0', _conflict_text)
                        _txt.config(state='disabled')
                        
                        # Modern button
                        _btn = _tk.Button(_container, text="Continue Merge Anyway",
                                           bg='#7c3aed', fg='#ffffff',
                                           font=("Segoe UI", 10, "bold"), relief='flat',
                                           padx=24, pady=10, cursor='hand2',
                                           activebackground='#6d28d9', activeforeground='#ffffff',
                                           command=lambda: (_win.destroy(), _done.set()))
                        _btn.pack(pady=(0, 0))
                        
                        _win.protocol("WM_DELETE_WINDOW", lambda: (_win.destroy(), _done.set()))
                    except Exception:
                        _done.set()
                self._root.after(0, _show_warn)
                _done.wait()
        except Exception as e:
            _logging.error("Pre-merge script conflict scan failed", exc_info=True)


        try:
            _logging.info("Step 1/4: Creating manifest")
            self._set_discord_merge_step("Step 1/4 — Creating manifest", "Building pack structure")
            self._update_progress(1, 5, "Step 1/4: Creating manifest...")
            self._create_manifest()
            self._update_progress(1, 25, "Step 1/4: Creating manifest... \u2713 Complete")
            _logging.info("Step 1/4 complete")
        except Exception as e:
            _logging.error("Step 1/4 _create_manifest failed", exc_info=True)
            self._update_progress(1, 25, f"Step 1/4: Error - {str(e)}")

        try:
            _logging.info("Step: _move_tick_and_delete_functions")
            self._move_tick_and_delete_functions()
        except Exception as e:
            _logging.error("_move_tick_and_delete_functions failed", exc_info=True)

        try:
            _logging.info(f"Step 2/4: Processing files ({len(new_selected_files)} addons)")
            self._set_discord_merge_step(f"Step 2/4 — Processing {len(new_selected_files)} addons", "Merging files")
            self._update_progress(2, 25, "Step 2/4: Processing files...")
            self._process_files(new_selected_files)
            self._update_progress(2, 50, "Step 2/4: Processing files... \u2713 Complete")
            _logging.info("Step 2/4 complete")
        except Exception as e:
            _logging.error("Step 2/4 _process_files failed", exc_info=True)
            self._update_progress(2, 50, f"Step 2/4: Error - {str(e)}")

        try:
            _logging.info("Step: _move_and_cleanup")
            self._move_and_cleanup()
        except Exception as e:
            _logging.error("_move_and_cleanup failed", exc_info=True)

        try:
            _logging.info("Step 3/4: Updating behavior pack")
            self._set_discord_merge_step("Step 3/4 — Updating behavior pack", "Wiring up scripts & data")
            self._update_progress(3, 50, "Step 3/4: Updating packs...")
            self._update_behavior_pack()
            self._update_progress(3, 75, "Step 3/4: Updating packs... \u2713 Complete")
            _logging.info("Step 3/4 complete")
        except Exception as e:
            _logging.error("Step 3/4 _update_behavior_pack failed", exc_info=True)
            self._update_progress(3, 75, f"Step 3/4: Error - {str(e)}")

        try:
            _logging.info("Step: _merge_flipbook_textures")
            self._merge_flipbook_textures(new_selected_files)
        except Exception as e:
            _logging.error("_merge_flipbook_textures failed", exc_info=True)

        try:
            _logging.info("Step: _merge_textures_list")
            self._merge_textures_list(new_selected_files)
        except Exception as e:
            _logging.error("_merge_textures_list failed", exc_info=True)

        try:
            # Extract and delete zip files
            self._extract_and_delete_zip_files()
        except Exception as e:
            _logging.error("_extract_and_delete_zip_files failed", exc_info=True)
            pass

        # Rename resource_pack.zip → resource_pack.mcpack BEFORE _move_to_resource_pack
        # so that function can actually find the file (it looks for .mcpack, not .zip).
        _rp_zip_early = _os.path.join(self._out_dir, "resource_pack.zip")
        _rp_mcpack_early = _os.path.join(self._out_dir, "resource_pack.mcpack")
        try:
            if _os.path.exists(_rp_zip_early) and not _os.path.exists(_rp_mcpack_early):
                _shutil.move(_rp_zip_early, _rp_mcpack_early)
        except Exception:
            pass

        try:
            # Step 4/4: Move to resource pack (final step)
            self._set_discord_merge_step("Step 4/4 — Finalizing", "Packaging the merged pack")
            self._update_progress(4, 75, "Step 4/4: Finalizing...")
            self._move_to_resource_pack()
            self._update_progress(4, 100, "Step 4/4: Finalizing... \u2713 Complete")
        except Exception as e:
            self._update_progress(4, 100, f"Step 4/4: Error - {str(e)}")
        finally:
            # Clean up any loose flipbook/textures_list files left by the legacy pipeline
            for _loose in ("flipbook_textures.json", "textures_list.json",
                           "flipbook_textures.zip", "textures_list.zip"):
                _loose_path = _os.path.join(self._out_dir, _loose)
                try:
                    if _os.path.isfile(_loose_path):
                        _os.remove(_loose_path)
                except Exception:
                    pass
            # Merge done — release the idle suppression flag so rotating messages resume
            self._discord_merging = False
            self._set_discord_merge_step("Merge complete", f"{len(new_selected_files)} addons packed")

        # Define paths for behavior and resource packs
        _bp_path = _os.path.join(self._out_dir, "behavior_pack.zip")
        _rp_path = _os.path.join(self._out_dir, "resource_pack.zip")
        
        _bp_new_path = _os.path.join(self._out_dir, "behavior_pack.mcpack")
        _rp_new_path = _os.path.join(self._out_dir, "resource_pack.mcpack")
        
        _scripts_path = _os.path.join(self._out_dir, "scripts")
        _temp_dir = _tempfile.mkdtemp(prefix='temp_unpack_')
        _tempr_dir = _tempfile.mkdtemp(prefix='temp_unpack_resource_pack_')
        _flipbook_textures_source = _os.path.join(self._out_dir, "flipbook_textures.json")
        _textures_list_source = _os.path.join(self._out_dir, "textures_list.json")
            

        try:
            # Move and rename the packs if they exist
            if _os.path.exists(_bp_path):
                _shutil.move(_bp_path, _bp_new_path)
        except Exception as e:
            log_error(e)
            _messagebox.showerror(_("msg.error"), _f("process.error_moving_behavior", error=str(e)))

        try:
            # resource_pack.zip may have already been renamed earlier; guard with existence check
            if _os.path.exists(_rp_path) and not _os.path.exists(_rp_new_path):
                _shutil.move(_rp_path, _rp_new_path)
        except Exception as e:
            log_error(e)
            _messagebox.showerror(_("msg.error"), _f("process.error_moving_resource", error=str(e)))

        try:
            if _os.path.exists(_scripts_path):
                _shutil.rmtree(_scripts_path)
        except Exception as e:
            pass

        try:
            if _os.path.exists(_temp_dir):
                _shutil.rmtree(_temp_dir)
        except Exception as e:
            pass

        try:
            if _os.path.exists(_tempr_dir):
                _shutil.rmtree(_tempr_dir)
        except Exception as e:
            pass

        try:
            if _os.path.exists(_flipbook_textures_source):
                _shutil.rmtree(_flipbook_textures_source)
        except Exception as e:
            pass
            

        try:
            if _os.path.exists(_textures_list_source):
                _shutil.rmtree(_textures_list_source)
        except Exception as e:
            pass
            
        # Cleanup: Delete the newly modified .mcpack files
        for new_file in new_mcpack_paths:
            try:
                if _os.path.exists(new_file):
                    _os.remove(new_file)
            except Exception:
                pass

        # Write merge manifest so user can view linked packs and remove one (re-merge without it)
        try:
            _manifest_path = _os.path.join(_output_dir, "_autobe_merge_manifest.json")
            _manifest_data = {
                "source_packs": [_os.path.abspath(p) for p in new_selected_files],
                "output_dir": _os.path.abspath(_output_dir),
            }
            with open(_manifest_path, "w", encoding="utf-8") as _fh:
                _json.dump(_manifest_data, _fh, indent=2)
        except Exception as _e:
            _logging.warning(f"Could not write merge manifest: {_e}")

        # Write merge report with validation checks for debugging common issues
        try:
            self._write_merge_report(
                _output_dir,
                _os.path.join(self._out_dir, "behavior_pack.mcpack"),
                _os.path.join(self._out_dir, "resource_pack.mcpack"),
                new_selected_files,
            )
        except Exception as _e:
            _logging.warning(f"Could not write merge report: {_e}")
