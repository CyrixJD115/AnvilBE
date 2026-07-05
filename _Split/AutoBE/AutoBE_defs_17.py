class AutoBEApp:

    def _update_behavior_pack(self):
        _bp_path = _os.path.join(self._out_dir, "behavior_pack.mcpack")
        _scripts_folder = _os.path.join(self._out_dir, "scripts")

        if _os.path.exists(_bp_path):
            _temp_dir = _tempfile.mkdtemp(prefix='temp_unpack_')
            _os.makedirs(_temp_dir, exist_ok=True)

            with _zipfile.ZipFile(_bp_path, 'r') as _zip_ref:
                _zip_ref.extractall(_temp_dir)

            _scripts_path_in_temp = _os.path.join(_temp_dir, "scripts")
            if (_os.path.exists(_scripts_path_in_temp)):
                _shutil.rmtree(_scripts_path_in_temp)
                
            _subpacks_path_in_temp = _os.path.join(_temp_dir, "subpacks")
            if (_os.path.exists(_subpacks_path_in_temp)):
                _shutil.rmtree(_subpacks_path_in_temp)

            if _os.path.isdir(_scripts_folder):
                _shutil.copytree(_scripts_folder, _scripts_path_in_temp)

            # Determine whether CodeNex.js contains real import statements.
            # If not (e.g. the "none" version group has no scripted packs),
            # strip the script module + script_eval capability + script API
            # dependencies from the manifest.  Bedrock refuses to load a BP
            # that declares @minecraft/server@1.13.0 (the fallback default)
            # because that version no longer exists in modern game builds.
            _codenex_path = _os.path.join(_scripts_path_in_temp, "CodeNex.js")
            _has_real_imports = False
            try:
                if _os.path.isfile(_codenex_path):
                    with open(_codenex_path, 'r', encoding='utf-8', errors='ignore') as _cj:
                        _has_real_imports = any(
                            line.strip().startswith('import ') for line in _cj
                        )
            except Exception:
                pass

            if not _has_real_imports:
                # Remove the now-useless scripts folder from the temp dir so
                # the empty CodeNex.js doesn't bloat the data-only output pack.
                try:
                    if _os.path.isdir(_scripts_path_in_temp):
                        _shutil.rmtree(_scripts_path_in_temp)
                except Exception:
                    pass
                # Patch the manifest to strip script-related entries.
                _manifest_tmp = _os.path.join(_temp_dir, "manifest.json")
                try:
                    with open(_manifest_tmp, 'r', encoding='utf-8') as _mf:
                        _mdata = _json.load(_mf)
                    # Remove script module entries
                    _mdata['modules'] = [
                        m for m in _mdata.get('modules', [])
                        if m.get('type') != 'script'
                    ]
                    # Remove script_eval capability
                    _caps = _mdata.get('capabilities', [])
                    if 'script_eval' in _caps:
                        _caps.remove('script_eval')
                    # Remove script API dependencies (@minecraft/server*, not uuid-based)
                    _script_mods = {'@minecraft/server', '@minecraft/server-ui',
                                    '@minecraft/server-gametest', '@minecraft/server-admin'}
                    _mdata['dependencies'] = [
                        d for d in _mdata.get('dependencies', [])
                        if d.get('module_name') not in _script_mods
                    ]
                    with open(_manifest_tmp, 'w', encoding='utf-8') as _mf:
                        _json.dump(_mdata, _mf, indent=2)
                    _logging.info("[_update_behavior_pack] No real imports — stripped script module from manifest.")
                except Exception as _me:
                    _logging.warning(f"[_update_behavior_pack] Could not patch manifest: {_me}")

            _new_bp_path = _os.path.join(self._out_dir, "behavior_pack.mcpack")
            with _zipfile.ZipFile(_new_bp_path, 'w') as _zip_ref:
                for _root, _dirs, _files in _os.walk(_temp_dir):
                    for _file in _files:
                        _file_path = _os.path.join(_root, _file)
                        _arcname = _os.path.relpath(_file_path, _temp_dir)
                        _zip_ref.write(_file_path, _arcname)

            _shutil.rmtree(_temp_dir)
            if _os.path.isdir(_scripts_folder):
                _shutil.rmtree(_scripts_folder)
            elif _os.path.exists(_scripts_folder):
                _os.remove(_scripts_folder)  # stale file artefact — remove it
            _logging.info("Process 3/4 Completed Successfully!")
        else:
            _logging.error("behavior_pack.mcpack not found", exc_info=True)
            _messagebox.showwarning("Error", "behavior_pack.mcpack not found")

    def _merge_flipbook_textures(self, _selected_files):
        if not _selected_files:
            _logging.error("No .mcpack files selected", exc_info=True)
            _messagebox.showerror(_("msg.error"), _("process.select_mcpacks_only"))
            return

        _merged_textures = []

        for _mcpack_file in _selected_files:
            try:
                with _zipfile.ZipFile(_mcpack_file, 'r') as _zip_ref:
                    try:
                        _texture_data = _zip_ref.read('textures/flipbook_textures.json').decode('latin-1')
                        _texture_data_lines = _texture_data.splitlines()
                        _filtered_texture_data = '\n'.join([_line for _line in _texture_data_lines if not _line.strip().startswith('//')])
                        try:
                            _textures_json = _json.loads(_filtered_texture_data)
                        except Exception:
                            continue
                        if isinstance(_textures_json, list):
                            _merged_textures.extend(_textures_json)
                    except KeyError:
                        pass
            except Exception as _e:
                _logging.error(f"An error occurred while merging flipbook textures: {_e}", exc_info=True)

        _merged_zip_path = _os.path.join(self._out_dir, "flipbook_textures.zip")
        with _zipfile.ZipFile(_merged_zip_path, 'w') as _merged_zip:
            _merged_zip.writestr('flipbook_textures.json', _json.dumps(_merged_textures))

    def _merge_textures_list(self, _selected_files):
        if not _selected_files:
            _logging.error("No .mcpack files selected", exc_info=True)
            _messagebox.showerror(_("msg.error"), _("process.select_mcpacks_only"))
            return

        _merged_textures = []

        for _mcpack_file in _selected_files:
            try:
                with _zipfile.ZipFile(_mcpack_file, 'r') as _zip_ref:
                    try:
                        _texture_data = _zip_ref.read('textures/textures_list.json').decode('latin-1')
                        _texture_data_lines = _texture_data.splitlines()
                        _filtered_texture_data = '\n'.join([_line for _line in _texture_data_lines if not _line.strip().startswith('//')])
                        try:
                            _textures_json = _json.loads(_filtered_texture_data)
                        except Exception:
                            continue
                        if isinstance(_textures_json, list):
                            _merged_textures.extend(_textures_json)
                    except KeyError:
                        pass
            except Exception as _e:
                _logging.error(f"An error occurred while merging textures list: {_e}", exc_info=True)

        _merged_zip_path = _os.path.join(self._out_dir, "textures_list.zip")
        with _zipfile.ZipFile(_merged_zip_path, 'w') as _merged_zip:
            _merged_zip.writestr('textures_list.json', _json.dumps(_merged_textures))

    def _extract_and_delete_zip_files(self):
        _flipbook_zip_path = _os.path.join(self._out_dir, "flipbook_textures.zip")
        _textures_zip_path = _os.path.join(self._out_dir, "textures_list.zip")

        try:
            with _zipfile.ZipFile(_flipbook_zip_path, 'r') as _flipbook_zip:
                _flipbook_zip.extract('flipbook_textures.json', self._out_dir)
        except FileNotFoundError:
            pass

        try:
            with _zipfile.ZipFile(_textures_zip_path, 'r') as _textures_zip:
                _textures_zip.extract('textures_list.json', self._out_dir)
        except FileNotFoundError:
            pass

        try:
            _os.remove(_flipbook_zip_path)
        except FileNotFoundError:
            pass

        try:
            _os.remove(_textures_zip_path)
        except FileNotFoundError:
            pass

    def _move_to_resource_pack(self):
        _rp_path = _os.path.join(self._out_dir, "resource_pack.mcpack")
        _textures_folder_name = "textures"

        if not _os.path.exists(_rp_path):
            _logging.warning("resource_pack.mcpack not found in output directory", exc_info=True)
            _messagebox.showwarning("Warning", "resource_pack.mcpack not found in output directory")
            return

        try:
            _temp_dir = _tempfile.mkdtemp(prefix='temp_unpack_resource_pack_')
            _os.makedirs(_temp_dir, exist_ok=True)
                
            with _zipfile.ZipFile(_rp_path, 'r') as _zip_ref:
                _zip_ref.extractall(_temp_dir)

            _functions_path_in_temp = _os.path.join(_temp_dir, "functions")
            if (_os.path.exists(_functions_path_in_temp)):
                _shutil.rmtree(_functions_path_in_temp)
                
            _entities_path_in_temp = _os.path.join(_temp_dir, "entities")
            if (_os.path.exists(_entities_path_in_temp)):
                _shutil.rmtree(_entities_path_in_temp)
                
            _subpacks_path_in_temp = _os.path.join(_temp_dir, "subpacks")
            if (_os.path.exists(_subpacks_path_in_temp)):
                _shutil.rmtree(_subpacks_path_in_temp)

            _textures_folder = _os.path.join(_temp_dir, _textures_folder_name)

            _flipbook_textures_source = _os.path.join(self._out_dir, "flipbook_textures.json")
            _flipbook_textures_dest = _os.path.join(_textures_folder, "flipbook_textures.json")
            _shutil.move(_flipbook_textures_source, _flipbook_textures_dest)

            _textures_list_source = _os.path.join(self._out_dir, "textures_list.json")
            _textures_list_dest = _os.path.join(_textures_folder, "textures_list.json")
            _shutil.move(_textures_list_source, _textures_list_dest)

            _new_rp_path = _os.path.join(self._out_dir, "updated_resource_pack.mcpack")
            with _zipfile.ZipFile(_new_rp_path, 'w') as _zip_ref:
                for _root, _dirs, _files in _os.walk(_temp_dir):
                    for _file in _files:
                        _file_path = _os.path.join(_root, _file)
                        _arcname = _os.path.relpath(_file_path, _temp_dir)
                        _zip_ref.write(_file_path, _arcname)

            _shutil.rmtree(_temp_dir)
            _shutil.move(_new_rp_path, _rp_path)
            _shutil.rmtree(_flipbook_textures_source)
            _shutil.rmtree(_textures_list_source)
            _logging.info("Process 4/4 Completed Successfully!")

        except Exception as _e:
            pass
            
    def _show_help(self):
        _help_window = _tk.Toplevel(self._root)
        self._apply_window_icon(_help_window)
        _help_window.title("Help")
        _help_window.geometry("800x800")
        _help_window.configure(bg='#0A0A0A')

        _help_text = """
        How To Use AutoBE
        
        Test Addons Individually:
        Test each addon individually in Minecraft before merging to check compatibility and functionality.
        
        Add Files:
        Click 'Add Files' to select .mcpack files you want to merge.
        Use Ctrl (or Cmd on Mac) to select multiple files.
        
        Check Packs:
        Click 'Check Packs' to see which Minecraft version each addon belongs to.
        Organize addons by version into separate folders (e.g., 1.16, 1.21, etc.).
        
        Merge by Version:
        Only merge addons from the same version (e.g., merge all 1.16 addons together).
        Do not merge addons from different versions (e.g., 1.16 with 1.21).
        
        Handling Single Addons:
        If an addon is the only one for its version, or if it breaks merged packs, handle it alone. 
        Add it without merging to resolve conflicts.
        
        Start Process:
        Click 'Browse' to select the output directory.
        Click 'Start Process' to merge selected packs.
        
        Testing and Troubleshooting:
        Test merged packs in Minecraft.
        If issues occur, remove problematic addons and add them separately.
        Re-merge compatible addons as needed.
        
        Important Notes:
        Always test addons before and after merging.
        Ensure you have rights to use or distribute the addons.
        
        CodeNex is not responsible for misuse of this tool.
        Property of CodeNex
        """

        _help_label = _tk.Label(_help_window, text=_help_text, bg='#0A0A0A', fg='#E1E1E1', font=("Helvetica", 12))
        _help_label.pack(padx=10, pady=10)

    def mcpacker_process_files(self, input_files, output_dir):
        import shutil
        failed, success, tempdirs = [], [], []
        total_files = len(input_files)
        
        # Get the selected mode
        mode = getattr(self, 'mcpacker_mode_var', _tk.StringVar(value="pack")).get()
        
        # Step 1: Reading Files
        self._root.after(0, lambda: self._update_mcpacker_progress(1, 10, f"Reading {total_files} file(s)..."))
        
        if mode == "extract":
            # Extraction mode: Extract .mcpack/.mcaddon files to folders
            self._root.after(0, lambda: self._update_mcpacker_progress(2, 25, "Preparing extraction..."))
            
            for idx, in_file in enumerate(input_files):
                try:
                    progress = 25 + int((idx / total_files) * 70)
                    file_name = _os.path.basename(in_file)
                    self._root.after(0, lambda p=progress, f=file_name: self._update_mcpacker_progress(2, p, f"Extracting: {f}..."))
                    
                    # Check if file is .mcpack or .mcaddon
                    if not in_file.lower().endswith(('.mcpack', '.mcaddon', '.zip')):
                        failed.append((in_file, "Not a .mcpack, .mcaddon, or .zip file"))
                        continue
                    
                    # Create output folder name
                    base_name = _os.path.splitext(_os.path.basename(in_file))[0]
                    out_folder = _os.path.join(output_dir, base_name)
                    
                    # If folder exists, add number suffix
                    counter = 1
                    original_out_folder = out_folder
                    while _os.path.exists(out_folder):
                        out_folder = f"{original_out_folder}_{counter}"
                        counter += 1
                    
                    # Extract the archive
                    with _zipfile.ZipFile(in_file, 'r') as zip_ref:
                        zip_ref.extractall(out_folder)
                    
                    success.append(out_folder)
                    
                except Exception as e:
                    failed.append((in_file, str(e)))
            
            # Step 4: Finalizing
            self._root.after(0, lambda: self._update_mcpacker_progress(4, 90, "Finalizing..."))
            
        else:
            # Pack mode: Original behavior - convert folders to .mcpack
            # Step 2: Finding Packs
            self._root.after(0, lambda: self._update_mcpacker_progress(2, 25, "Finding valid packs in files..."))
            all_packs = []
            for idx, in_file in enumerate(input_files):
                try:
                    progress = 25 + int((idx / total_files) * 30)
                    self._root.after(0, lambda p=progress, f=_os.path.basename(in_file): self._update_mcpacker_progress(2, p, f"Finding packs in: {f}..."))
                    packs = find_valid_packs(in_file)
                    if not packs:
                        failed.append((in_file, "No manifest.json found"))
                        continue
                    all_packs.append((in_file, packs))
                except Exception as e:
                    failed.append((in_file, str(e)))
            
            # Step 3: Packaging Files
            self._root.after(0, lambda: self._update_mcpacker_progress(3, 55, "Packaging files into MCPACK format..."))
            
            total_packs = sum(len(packs) for _, packs in all_packs)
            pack_count = 0
            for in_file, packs in all_packs:
                for pack_folder in packs:
                    try:
                        base_name = _os.path.splitext(_os.path.basename(in_file))[0]
                        out_name = base_name + ".mcpack"
                        if len(packs) > 1:
                            idx = packs.index(pack_folder) + 1
                            out_name = f"{base_name}_{idx}.mcpack"
                        out_path = _os.path.join(output_dir, out_name)
                        
                        progress = 55 + int((pack_count / total_packs) * 35) if total_packs > 0 else 55
                        self._root.after(0, lambda p=progress, n=out_name: self._update_mcpacker_progress(3, p, f"Packaging: {n}..."))
                        
                        zip_pack_folder(pack_folder, out_path)
                        success.append(out_path)
                        if pack_folder.startswith(_tempfile.gettempdir()):
                            tempdirs.append(pack_folder)
                        pack_count += 1
                    except Exception as e:
                        failed.append((in_file, str(e)))
            
            # Step 4: Finalizing
            self._root.after(0, lambda: self._update_mcpacker_progress(4, 90, "Finalizing and cleaning up..."))
        for d in tempdirs:
            try:
                shutil.rmtree(d)
            except:
                pass
        
        # Show completion message in progress display
        if failed:
            failed_list = "\n".join([f"- {_os.path.basename(fname)}: {reason}" for fname, reason in failed[:5]])
            if len(failed) > 5:
                failed_list += f"\n... and {len(failed) - 5} more"
            if mode == "extract":
                message = f"Completed: {len(success)} extracted, {len(failed)} failed"
                self._root.after(0, lambda: self._update_mcpacker_progress(4, 100, message))
                error_msg = f"Extracted {len(success)} folder(s).\n\nFailed files:\n{failed_list}"
                self._root.after(0, lambda: _messagebox.showerror(_("mcpacker.some_files_failed"), error_msg))
            else:
                message = f"Completed: {len(success)} exported, {len(failed)} failed"
                self._root.after(0, lambda: self._update_mcpacker_progress(4, 100, message))
                error_msg = f"Exported {len(success)} MCPACK(s).\n\nFailed files:\n{failed_list}"
                self._root.after(0, lambda: _messagebox.showerror(_("mcpacker.some_files_failed"), error_msg))
        else:
            if mode == "extract":
                message = f"Successfully extracted {len(success)} folder(s)! ✓"
                self._root.after(0, lambda: self._update_mcpacker_progress(4, 100, message))
            else:
                message = f"Successfully exported {len(success)} MCPACK(s)! ✓"
                self._root.after(0, lambda: self._update_mcpacker_progress(4, 100, message))

    def _update_mcpacker_progress(self, step, progress_percent, message):
        """Update the MCPACKER progress display with current step and message."""
        if hasattr(self, '_mcpacker_progress_step_label'):
            self._mcpacker_progress_step_label.config(text=message)
            self._mcpacker_progress['value'] = progress_percent
            self._root.update_idletasks()
            
            # Update step indicators
            if hasattr(self, '_mcpacker_step_labels') and 1 <= step <= 4:
                for i in range(4):
                    if i < step - 1:
                        # Completed steps
                        self._mcpacker_step_labels[i]['status'].config(text="✓", fg='#9333ea')
                        self._mcpacker_step_labels[i]['label'].config(fg='#FFFFFF')
                    elif i == step - 1:
                        # Current step
                        self._mcpacker_step_labels[i]['status'].config(text="→", fg='#9333ea')
                        self._mcpacker_step_labels[i]['label'].config(fg='#9333ea')
                    else:
                        # Pending steps
                        self._mcpacker_step_labels[i]['status'].config(text="○", fg='#666666')
                        self._mcpacker_step_labels[i]['label'].config(fg='#999999')
                # Mark all as complete if step 4 is done
                if step == 4:
                    for i in range(4):
                        self._mcpacker_step_labels[i]['status'].config(text="✓", fg='#9333ea')
                        self._mcpacker_step_labels[i]['label'].config(fg='#FFFFFF')

    def _set_mcpacker_mode(self, mode):
        """Set the MCPACKER processing mode."""
        _logging.debug(f"_set_mcpacker_mode called with mode: {mode}")
        self.mcpacker_mode_var.set(mode)
        self._update_mcpacker_mode_labels()
        # Settings will be saved automatically via trace_add
    
    
    def _update_mcpacker_mode_labels(self):
        """Update step labels based on selected mode."""
        if hasattr(self, '_mcpacker_step_labels') and len(self._mcpacker_step_labels) >= 4:
            mode = self.mcpacker_mode_var.get()
            if mode == "extract":
                self._mcpacker_step_labels[2]['label'].config(text=_("mcpacker.extracting"))
            else:
                self._mcpacker_step_labels[2]['label'].config(text=_("mcpacker.packaging"))
    
    def _reset_mcpacker_progress(self):
        """Reset MCPACKER progress display to initial state."""
        if hasattr(self, '_mcpacker_progress_step_label'):
            self._mcpacker_progress_step_label.config(text=_("app.ready_to_process"))
            self._mcpacker_progress['value'] = 0
            if hasattr(self, '_mcpacker_step_labels'):
                for step_info in self._mcpacker_step_labels:
                    step_info['status'].config(text="○", fg='#666666')
                    step_info['label'].config(fg='#999999')

    def start_mcpacker(self):
        files = self._mcpacker_files  # Use stored file paths
        output_dir = self.output_dir_var.get()
        if not files or not output_dir:
            _messagebox.showerror(_("msg.error"), _("process.select_files_and_output"))
            return
        
        # Disable start button during processing
        self._btn_mcpacker_start.config(state='disabled')
        
        # Run processing in a separate thread to prevent UI freezing
        def process_thread():
            try:
                self._root.after(0, lambda: self._reset_mcpacker_progress())
                self._root.after(0, lambda: self._update_mcpacker_progress(0, 0, "Initializing process..."))
                self.mcpacker_process_files(files, output_dir)
                self._root.after(0, lambda: self._update_mcpacker_progress(4, 100, "Processing completed successfully! ✓"))
                # Clear selected files and output so tab is ready for next run
                self._root.after(0, lambda: self._reset_mcpacker_list())
                
            except Exception as e:
                _logging.error("An error occurred during MCPACKER process", exc_info=True)
                self._root.after(0, lambda: _messagebox.showerror(_("msg.error"), _f("process.an_error_occurred", error=e)))
                self._root.after(0, lambda: self._update_mcpacker_progress(0, 0, f"Error: {str(e)}"))
            finally:
                # Re-enable start button
                self._root.after(0, lambda: self._btn_mcpacker_start.config(state='normal'))
        
        threading.Thread(target=process_thread, daemon=True).start()
