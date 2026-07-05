class AutoBEApp:

    def _create_tooltip(self, widget, text):
        """Create a tooltip for a widget."""
        def on_enter(event):
            # Don't show tooltip if widget is being destroyed
            try:
                if not widget.winfo_exists():
                    return
            except:
                return
            
            # Clean up any existing tooltip first
            if hasattr(widget, 'tooltip'):
                try:
                    if widget.tooltip.winfo_exists():
                        widget.tooltip.destroy()
                except:
                    pass
                try:
                    delattr(widget, 'tooltip')
                except:
                    pass
            
            tooltip = _tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.configure(bg='#1a1a1a', highlightthickness=1, highlightbackground='#9333ea')
            tooltip.attributes('-topmost', True)
            # Wrap long text so tooltip stays on screen; max width ~320px
            wrap = 320
            label = _tk.Label(tooltip, text=text, bg='#1a1a1a', fg='#FFFFFF', font=("Segoe UI", 9), padx=8, pady=4, justify='left', wraplength=wrap)
            label.pack()
            tooltip.update_idletasks()
            w = tooltip.winfo_reqwidth()
            h = tooltip.winfo_reqheight()
            margin = 16
            try:
                sw = self._root.winfo_screenwidth()
                sh = self._root.winfo_screenheight()
            except Exception:
                sw, sh = 800, 600
            x = widget.winfo_rootx() + 20
            y = widget.winfo_rooty() + 20
            if x + w + margin > sw:
                x = sw - w - margin
            if x < margin:
                x = margin
            if y + h + margin > sh:
                y = sh - h - margin
            if y < margin:
                y = margin
            tooltip.geometry(f"+{x}+{y}")
            widget.tooltip = tooltip
        
        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                try:
                    if widget.tooltip.winfo_exists():
                        widget.tooltip.destroy()
                except:
                    pass
                try:
                    delattr(widget, 'tooltip')
                except:
                    pass
        
        def on_destroy(event):
            """Clean up tooltip when widget is destroyed."""
            if hasattr(widget, 'tooltip'):
                try:
                    if widget.tooltip.winfo_exists():
                        widget.tooltip.destroy()
                except:
                    pass
                try:
                    delattr(widget, 'tooltip')
                except:
                    pass
        
        widget.bind('<Enter>', on_enter)
        widget.bind('<Leave>', on_leave)
        widget.bind('<Destroy>', on_destroy)
    
    def init_settings_tab(self):
        """Initialize Settings tab - empty frame, dropdown shown on click."""
        # Empty frame - we'll show dropdown when tab is clicked
        self.settings_frame.configure(bg='#000000')
    
    def _close_settings_dropdown(self):
        """Close settings dropdown and clean up all tooltips."""
        try:
            if hasattr(self, '_settings_dropdown'):
                try:
                    if self._settings_dropdown.winfo_exists():
                        # Clean up all tooltips recursively
                        def cleanup_tooltips(widget):
                            """Recursively clean up tooltips."""
                            try:
                                if hasattr(widget, 'tooltip'):
                                    try:
                                        if widget.tooltip.winfo_exists():
                                            widget.tooltip.destroy()
                                    except:
                                        pass
                                    try:
                                        delattr(widget, 'tooltip')
                                    except:
                                        pass
                                for child in widget.winfo_children():
                                    cleanup_tooltips(child)
                            except:
                                pass
                        
                        if getattr(self, "_settings_marquee_after_id", None) is not None:
                            try:
                                self._root.after_cancel(self._settings_marquee_after_id)
                            except Exception:
                                pass
                            self._settings_marquee_after_id = None
                        cleanup_tooltips(self._settings_dropdown)
                        self._settings_dropdown.destroy()
                except:
                    pass
                try:
                    delattr(self, '_settings_dropdown')
                except:
                    pass
                try:
                    if hasattr(self, '_settings_vol_value_label'):
                        delattr(self, '_settings_vol_value_label')
                except:
                    pass
                try:
                    if hasattr(self, '_settings_refresh_now_playing'):
                        delattr(self, '_settings_refresh_now_playing')
                except:
                    pass
                
                # Unbind click handler
                try:
                    self._root.unbind('<Button-1>')
                except:
                    pass
        except Exception as e:
            log_error(f"Error closing settings dropdown: {e}")
    
    def _on_notebook_click(self, event):
        """Intercept notebook clicks to prevent Settings tab from switching."""
        try:
            # Find which tab was clicked
            x, y = event.x, event.y
            clicked_tab = self.notebook.index(f"@{x},{y}")
            
            # Find Settings tab index
            total_tabs = self.notebook.index("end")
            settings_index = None
            for i in range(total_tabs):
                try:
                    if self.notebook.tab(i, "text") == _("tabs.settings"):
                        settings_index = i
                        break
                except:
                    continue
            
            # If Settings tab was clicked, prevent tab change and show dropdown
            if settings_index is not None and clicked_tab == settings_index:
                # Store current tab before it changes
                current_tab = self.notebook.index(self.notebook.select())
                if current_tab != settings_index:
                    if not hasattr(self, '_last_tab_index'):
                        self._last_tab_index = current_tab
                    # Prevent tab change by switching back after event
                    self._root.after_idle(lambda: self.notebook.select(self._last_tab_index))
                
                # Show dropdown
                self._root.after(10, self._show_settings_dropdown)
                return "break"  # Prevent default tab change
        except Exception as e:
            # If we can't determine which tab, let it proceed normally
            pass
    
    def _on_settings_tab_click(self, event=None):
        """Legacy handler - no longer used but kept for compatibility."""
        pass
    
    def _show_settings_dropdown(self):
        """Show settings dropdown menu."""
        try:
            # Close existing dropdown if open
            self._close_settings_dropdown()
            
            # Get notebook and app window positions
            self.notebook.update_idletasks()
            self._root.update_idletasks()
            
            notebook_x = self.notebook.winfo_rootx()
            notebook_y = self.notebook.winfo_rooty()
            notebook_width = self.notebook.winfo_width()
            
            app_x = self._root.winfo_rootx()
            app_y = self._root.winfo_rooty()
            app_width = self._root.winfo_width()
            app_height = self._root.winfo_height()
            
            # Find Settings tab position dynamically
            total_tabs = self.notebook.index("end")
            settings_tab_index = None
            for i in range(total_tabs):
                if self.notebook.tab(i, "text") == _("tabs.settings"):
                    settings_tab_index = i
                    break
            
            if settings_tab_index is None:
                settings_tab_index = 4  # Fallback
            
            # Approximate tab width (notebook width / number of tabs)
            tab_width = notebook_width / total_tabs if total_tabs > 0 else 100
            tab_x = notebook_x + (settings_tab_index * tab_width) + (tab_width / 2)
            tab_y = notebook_y + 35  # Below tab bar
            
            # Create dropdown menu (Toplevel - proper menu panel)
            self._settings_dropdown = _tk.Toplevel(self._root)
            self._settings_dropdown.wm_overrideredirect(True)
            self._settings_dropdown.configure(bg='#9333ea')  # Border color
            
            # Fit dropdown to window: width within app, height within app
            menu_width = min(400, max(320, app_width - 80))
            menu_height = min(520, max(380, app_height - 80))
            
            dropdown_x = int(tab_x - menu_width // 2)
            dropdown_y = int(tab_y)
            if dropdown_x < app_x:
                dropdown_x = app_x + 10
            if dropdown_x + menu_width > app_x + app_width:
                dropdown_x = app_x + app_width - menu_width - 10
            if dropdown_y + menu_height > app_y + app_height:
                dropdown_y = app_y + app_height - menu_height - 10
            
            self._settings_dropdown.geometry(f"{menu_width}x{menu_height}+{dropdown_x}+{dropdown_y}")
            self._settings_dropdown.attributes('-topmost', False)
            self._settings_dropdown.transient(self._root)
            try:
                self._settings_dropdown.deiconify()
            except:
                pass
            self._settings_dropdown.lift(self._root)
            self._settings_dropdown.update_idletasks()
            
            # Inner: panel with scrollable content (hover + mouse wheel to scroll)
            inner = _tk.Frame(self._settings_dropdown, bg='#252525', highlightthickness=0)
            inner.place(x=2, y=2, width=menu_width-4, height=menu_height-4)
            inner.grid_rowconfigure(1, weight=1)
            inner.grid_columnconfigure(0, weight=1)

            # ── Header row: title + close button ────────────────────────────
            _hdr = _tk.Frame(inner, bg='#1e1e1e', height=26)
            _hdr.grid(row=0, column=0, sticky='ew')
            _hdr.grid_propagate(False)
            _tk.Label(_hdr, text="⚙  Settings",
                      bg='#1e1e1e', fg='#aaaaaa',
                      font=("Segoe UI", 9)).place(x=10, rely=0.5, anchor='w')
            _tk.Button(
                _hdr, text='✕',
                bg='#1e1e1e', fg='#666666',
                font=("Segoe UI", 9, "bold"),
                relief='flat', cursor='hand2',
                activebackground='#7f1d1d', activeforeground='#FFFFFF',
                padx=6, pady=0,
                command=self._close_settings_dropdown
            ).place(relx=1.0, rely=0.5, anchor='e')

            canvas = _tk.Canvas(inner, bg='#252525', highlightthickness=0)
            canvas.grid(row=1, column=0, sticky='nsew')
            content_outer = _tk.Frame(canvas, bg='#252525')
            content = _tk.Frame(content_outer, bg='#252525')
            content.pack(fill='both', expand=True, padx=16, pady=16)
            canvas_window = canvas.create_window(0, 0, window=content_outer, anchor='nw')
            def _on_content_configure(event):
                canvas.configure(scrollregion=canvas.bbox('all'))
            content_outer.bind('<Configure>', _on_content_configure)
            def _on_canvas_configure(event):
                canvas.itemconfig(canvas_window, width=event.width)
            canvas.bind('<Configure>', _on_canvas_configure)
            def _on_mousewheel(event):
                if self._settings_dropdown.winfo_exists():
                    canvas.yview_scroll(int(-1 * (event.delta / 120)), 'units')
            def _scroll_bind_enter(event):
                canvas.bind_all('<MouseWheel>', _on_mousewheel)
            def _scroll_bind_leave(event):
                try:
                    canvas.unbind_all('<MouseWheel>')
                except Exception:
                    pass
            canvas.bind('<Enter>', _scroll_bind_enter)
            canvas.bind('<Leave>', _scroll_bind_leave)
            
            # ---- Section 1: App language (stacked vertically so all are visible and clickable) ----
            lang_label = _tk.Label(content, text=_("settings.app_language"), bg='#252525', fg='#E5E7EB',
                                  font=("Segoe UI", 11, "bold"))
            lang_label.pack(anchor='w', pady=(0, 8))
            lang_btn_frame = _tk.Frame(content, bg='#252525')
            lang_btn_frame.pack(fill='x', pady=(0, 14))
            def set_lang(lang):
                self._current_lang = lang
                self._save_settings()
                _tr_load(lang)
                self._close_settings_dropdown()
                self._show_themed_info_dialog(_("update.title"), _("settings.language_saved"))
            for code, label_key in [("en", "lang.english"), ("es", "lang.spanish"), ("zh", "lang.chinese"), ("id", "lang.indonesian"), ("ru", "lang.russian"), ("pt", "lang.portuguese_br")]:
                b = _tk.Button(lang_btn_frame, text=_(label_key), command=lambda c=code: set_lang(c),
                              bg='#3a3a3a', fg='#FFFFFF', font=("Segoe UI", 10), relief='flat', cursor='hand2',
                              activebackground='#9333ea', activeforeground='#FFFFFF', padx=14, pady=8, anchor='w')
                b.pack(fill='x', pady=(0, 4))
            
            _tk.Frame(content, bg='#404040', height=2).pack(fill='x', pady=(0, 12))
            
            # ---- Section 2: MCPACKER mode ----
            setting_label = _tk.Label(content, text=_("settings.mcpacker_mode"), bg='#252525', fg='#E5E7EB',
                                      font=("Segoe UI", 11, "bold"))
            setting_label.pack(anchor='w', pady=(0, 8))
            self._create_tooltip(setting_label, "Choose how MCPACKER processes files:\n• Pack: Converts folders to .mcpack files\n• Extract: Unzips .mcpack/.mcaddon/.zip files to folders")
            
            mode_frame = _tk.Frame(content, bg='#252525')
            mode_frame.pack(fill='x', pady=(0, 14))
            current_mode = self.mcpacker_mode_var.get()
            def close_dropdown_and_set_mode(mode):
                self._set_mcpacker_mode(mode)
                self._close_settings_dropdown()
            
            pack_container = _tk.Frame(mode_frame, bg='#252525')
            pack_container.pack(fill='x', pady=(0, 6))
            pack_check = _tk.Label(pack_container, text="✓" if current_mode == "pack" else "○", bg='#252525',
                                  fg='#9333ea' if current_mode == "pack" else '#666666', font=("Segoe UI", 12), width=2)
            pack_check.pack(side='left', padx=(0, 10))
            pack_btn = _tk.Button(pack_container, text=_("settings.pack"), command=lambda: close_dropdown_and_set_mode("pack"),
                                 bg='#3a3a3a', fg='#FFFFFF', font=("Segoe UI", 10, "bold" if current_mode == "pack" else "normal"),
                                 relief='flat', cursor='hand2', activebackground='#9333ea', activeforeground='#FFFFFF',
                                 padx=14, pady=8, anchor='w')
            pack_btn.pack(side='left', fill='x', expand=True)
            self._create_tooltip(pack_btn, "Converts folder structures into .mcpack files")
            
            extract_container = _tk.Frame(mode_frame, bg='#252525')
            extract_container.pack(fill='x')
            extract_check = _tk.Label(extract_container, text="✓" if current_mode == "extract" else "○", bg='#252525',
                                      fg='#9333ea' if current_mode == "extract" else '#666666', font=("Segoe UI", 12), width=2)
            extract_check.pack(side='left', padx=(0, 10))
            extract_btn = _tk.Button(extract_container, text=_("settings.extract"), command=lambda: close_dropdown_and_set_mode("extract"),
                                    bg='#3a3a3a', fg='#FFFFFF', font=("Segoe UI", 10, "bold" if current_mode == "extract" else "normal"),
                                    relief='flat', cursor='hand2', activebackground='#9333ea', activeforeground='#FFFFFF',
                                    padx=14, pady=8, anchor='w')
            extract_btn.pack(side='left', fill='x', expand=True)
            self._create_tooltip(extract_btn, "Unzips .mcpack/.mcaddon/.zip files into folder structures")
            
            if current_mode == "pack":
                pack_btn.config(bg='#9333ea', fg='#FFFFFF')
            else:
                extract_btn.config(bg='#9333ea', fg='#FFFFFF')
            
            _tk.Frame(content, bg='#404040', height=2).pack(fill='x', pady=(0, 12))
            
            # ---- Section 2b: Merge by script version (AutoBE tab) ----
            content_width = menu_width - 4 - 32
            merge_by_ver_label = _tk.Label(content, text=_("settings.merge_by_version"), bg='#252525', fg='#E5E7EB',
                                           font=("Segoe UI", 11, "bold"), wraplength=content_width, justify='left')
            merge_by_ver_label.pack(anchor='w', pady=(0, 8))
            self._create_tooltip(merge_by_ver_label, _("settings.merge_by_version_tooltip"))
            merge_by_ver_cb = _tk.Checkbutton(content, text=_("settings.merge_by_version_check"),
                                              variable=self.merge_by_version_var, bg='#252525', fg='#FFFFFF',
                                              selectcolor='#1a1a1a', activebackground='#252525', activeforeground='#FFFFFF',
                                              font=("Segoe UI", 10), relief='flat', cursor='hand2',
                                              wraplength=content_width, justify='left')
            merge_by_ver_cb.pack(anchor='w', pady=(0, 14))
            
            _tk.Frame(content, bg='#404040', height=2).pack(fill='x', pady=(0, 12))
            
            # ---- Section 2c: Customize merged pack after merge ----
            content_width_custom = menu_width - 4 - 32
            custom_label = _tk.Label(content, text=_("settings.customize_pack_after_merge") if _("settings.customize_pack_after_merge") != "settings.customize_pack_after_merge" else "Name merged pack after merge", bg='#252525', fg='#E5E7EB', font=("Segoe UI", 11, "bold"), wraplength=content_width_custom, justify='left')
            custom_label.pack(anchor='w', pady=(0, 8))
            self._create_tooltip(custom_label, _("settings.customize_pack_after_merge_tooltip") if _("settings.customize_pack_after_merge_tooltip") != "settings.customize_pack_after_merge_tooltip" else "After merge completes, prompt to set pack name, description, and icon.")
            custom_cb = _tk.Checkbutton(content, text=_("settings.customize_pack_after_merge_check") if _("settings.customize_pack_after_merge_check") != "settings.customize_pack_after_merge_check" else "Prompt to name pack and pick icon after merge",
                                        variable=self.customize_pack_after_merge_var, bg='#252525', fg='#FFFFFF',
                                        selectcolor='#1a1a1a', activebackground='#252525', activeforeground='#FFFFFF',
                                        font=("Segoe UI", 10), relief='flat', cursor='hand2',
                                        wraplength=content_width_custom, justify='left')
            custom_cb.pack(anchor='w', pady=(0, 14))
            
            _tk.Frame(content, bg='#404040', height=2).pack(fill='x', pady=(0, 12))
            
            # ---- Section 2d: Show linked packs after merge ----
            linked_label = _tk.Label(content, text=_("settings.show_linked_packs_after_merge") if _("settings.show_linked_packs_after_merge") != "settings.show_linked_packs_after_merge" else "Show linked packs after merge", bg='#252525', fg='#E5E7EB', font=("Segoe UI", 11, "bold"), wraplength=content_width_custom, justify='left')
            linked_label.pack(anchor='w', pady=(0, 8))
            self._create_tooltip(linked_label, _("settings.show_linked_packs_after_merge_tooltip") if _("settings.show_linked_packs_after_merge_tooltip") != "settings.show_linked_packs_after_merge_tooltip" else "After merge, show the list of addons in this merge so you can view or remove one.")
            linked_cb = _tk.Checkbutton(content, text=_("settings.show_linked_packs_after_merge_check") if _("settings.show_linked_packs_after_merge_check") != "settings.show_linked_packs_after_merge_check" else "Show linked packs list after merge",
                                        variable=self.show_linked_packs_after_merge_var, bg='#252525', fg='#FFFFFF',
                                        selectcolor='#1a1a1a', activebackground='#252525', activeforeground='#FFFFFF',
                                        font=("Segoe UI", 10), relief='flat', cursor='hand2',
                                        wraplength=content_width_custom, justify='left')
            linked_cb.pack(anchor='w', pady=(0, 14))

            _tk.Frame(content, bg='#404040', height=2).pack(fill='x', pady=(0, 12))

            # ---- Section 2e: ExtendedBE addon fixer ----
            _ebe_fixer_count = len(_EXTENDEDBE_FIXERS)
            _ebe_tooltip = (
                f"Repairs known bugs and outdated code in addons before merging.\n"
                f"Fixes things like misplaced files, broken events, missing definitions,\n"
                f"and outdated sound entries — without modifying the original .mcpack.\n\n"
                f"{_ebe_fixer_count} fixer{'s' if _ebe_fixer_count != 1 else ''} currently loaded  |  AutoBE/extendedbe/"
            )
            _ebe_label = _tk.Label(content,
                                   text="Addon Fixer",
                                   bg='#252525', fg='#E5E7EB',
                                   font=("Segoe UI", 11, "bold"),
                                   wraplength=content_width_custom, justify='left')
            _ebe_label.pack(anchor='w', pady=(0, 2))
            _tk.Label(content,
                      text="Auto-repairs broken or outdated addons before merging",
                      bg='#252525', fg='#6b7280',
                      font=("Segoe UI", 9),
                      wraplength=content_width_custom, justify='left').pack(anchor='w', pady=(0, 8))
            self._create_tooltip(_ebe_label, _ebe_tooltip)
            _ebe_cb = _tk.Checkbutton(content,
                                      text="Enable addon fixer",
                                      variable=self.extendedbe_enabled_var,
                                      bg='#252525', fg='#FFFFFF',
                                      selectcolor='#1a1a1a',
                                      activebackground='#252525', activeforeground='#FFFFFF',
                                      font=("Segoe UI", 10), relief='flat', cursor='hand2',
                                      wraplength=content_width_custom, justify='left')
            self._create_tooltip(_ebe_cb, _ebe_tooltip)
            _ebe_cb.pack(anchor='w', pady=(0, 14))

            _tk.Frame(content, bg='#404040', height=2).pack(fill='x', pady=(0, 12))

            # ---- Section 2f: Modpack Organization (Excel/CSV) ----
            excel_tooltip = (
                "Automatically organize your addons into Excel/CSV files for better management.\n"
                "Each modpack gets its own sheet with addon details, versions, and compatibility info.\n"
                "Enables easy tracking, sharing, and management of your modpack configurations.\n"
                "Uses CSV format by default (works in Excel without additional dependencies)."
            )
            excel_label = _tk.Label(content,
                                   text="Modpack Organization",
                                   bg='#252525', fg='#E5E7EB',
                                   font=("Segoe UI", 11, "bold"),
                                   wraplength=content_width_custom, justify='left')
            excel_label.pack(anchor='w', pady=(0, 2))
            _tk.Label(content,
                      text="Track addons, versions, and compatibility in Excel/CSV files",
                      bg='#252525', fg='#6b7280',
                      font=("Segoe UI", 9),
                      wraplength=content_width_custom, justify='left').pack(anchor='w', pady=(0, 8))
            self._create_tooltip(excel_label, excel_tooltip)
            excel_cb = _tk.Checkbutton(content,
                                      text="Enable Excel/CSV organization",
                                      variable=self.modpack_organization_var,
                                      bg='#252525', fg='#FFFFFF',
                                      selectcolor='#1a1a1a',
                                      activebackground='#252525', activeforeground='#FFFFFF',
                                      font=("Segoe UI", 10), relief='flat', cursor='hand2',
                                      wraplength=content_width_custom, justify='left')
            self._create_tooltip(excel_cb, excel_tooltip)
            excel_cb.pack(anchor='w', pady=(0, 14))


            _tk.Frame(content, bg='#404040', height=2).pack(fill='x', pady=(0, 12))

            # ---- Section 2e: Background music ----
            music_label = _tk.Label(content, text="Background music" if _("settings.background_music") == "settings.background_music" else _("settings.background_music"), bg='#252525', fg='#E5E7EB', font=("Segoe UI", 11, "bold"), wraplength=content_width_custom, justify='left')
            music_label.pack(anchor='w', pady=(0, 8))
            self._create_tooltip(music_label, _("settings.background_music_tooltip") if _("settings.background_music_tooltip") != "settings.background_music_tooltip" else "Play non-copyright lofi-style music from the music/ folder (e.g. background.ogg). Requires pygame.")
            music_cb = _tk.Checkbutton(content, text="Play background music" if _("settings.background_music_check") == "settings.background_music_check" else _("settings.background_music_check"),
                                        variable=self.background_music_var, bg='#252525', fg='#FFFFFF',
                                        selectcolor='#1a1a1a', activebackground='#252525', activeforeground='#FFFFFF',
                                        font=("Segoe UI", 10), relief='flat', cursor='hand2',
                                        wraplength=content_width_custom, justify='left')
            music_cb.pack(anchor='w', pady=(0, 8))
            # Playlist selector from music subfolders (music/<playlist-name>/...)
            _playlist_label = _tk.Label(content, text="Playlist", bg='#252525', fg='#E5E7EB', font=("Segoe UI", 10))
            _playlist_label.pack(anchor='w', pady=(0, 4))
            playlist_values = ["__all__"] + self._get_available_music_playlists()
            current_playlist = self._sanitize_playlist_key(
                getattr(self, "music_playlist_var", _tk.StringVar(value="__all__")).get()
            )
            if current_playlist not in playlist_values:
                current_playlist = "__all__"
            _playlist_labels = [("All music" if p == "__all__" else p) for p in playlist_values]
            _playlist_label_to_value = {
                ("All music" if p == "__all__" else p): p for p in playlist_values
            }
            _playlist_ui_var = _tk.StringVar(
                value=("All music" if current_playlist == "__all__" else current_playlist)
            )
            playlist_combo = _ttk.Combobox(
                content,
                textvariable=_playlist_ui_var,
                values=_playlist_labels,
                state="readonly",
                width=36,
            )
            playlist_combo.pack(anchor='w', pady=(0, 8), fill='x')
            def _on_playlist_pick(event=None):
                try:
                    picked_label = _playlist_ui_var.get()
                    picked_value = _playlist_label_to_value.get(picked_label, "__all__")
                    picked_value = self._sanitize_playlist_key(picked_value)
                    if getattr(self, "music_playlist_var", None) and self.music_playlist_var.get() != picked_value:
                        self.music_playlist_var.set(picked_value)
                except Exception:
                    pass
            playlist_combo.bind("<<ComboboxSelected>>", _on_playlist_pick)
            self._create_tooltip(
                playlist_combo,
                "Choose a music playlist folder from music/. Use 'All music' to play everything."
            )
            music_vol_label = _tk.Label(content, text="Music volume" if _("settings.music_volume") == "settings.music_volume" else _("settings.music_volume"), bg='#252525', fg='#E5E7EB', font=("Segoe UI", 10), wraplength=content_width_custom, justify='left')
            music_vol_label.pack(anchor='w', pady=(0, 4))
            # Use ttk.Scale to avoid hover glitching (tk.Scale redraws/jumps on hover). Custom style is created, not a theme.
            _vol_style_name = "DarkVol.Horizontal.TScale"
            try:
                _s = _ttk.Style()
                _s.configure(_vol_style_name, background='#252525', troughcolor='#404040')
                _s.map(_vol_style_name, background=[('active', '#9333ea')])
            except Exception:
                pass
            try:
                music_vol_scale = _ttk.Scale(content, from_=0, to=100, orient=_tk.HORIZONTAL, variable=self.background_music_volume_var, length=200, style=_vol_style_name)
            except Exception:
                music_vol_scale = _tk.Scale(content, from_=0, to=100, orient=_tk.HORIZONTAL, variable=self.background_music_volume_var, bg='#252525', fg='#E5E7EB', troughcolor='#404040', highlightthickness=0, activebackground='#252525', length=200, showvalue=False, resolution=5, takefocus=0, sliderrelief='flat', bd=0)
            music_vol_scale.pack(anchor='w', pady=(0, 4))
            _vol_value_label = _tk.Label(content, text=str(getattr(self, "background_music_volume_var", _tk.IntVar(value=70)).get()) + "%", bg='#252525', fg='#E5E7EB', font=("Segoe UI", 9))
            _vol_value_label.pack(anchor='w', pady=(0, 2))
            self._settings_vol_value_label = _vol_value_label  # updated by existing volume trace when dropdown open
            # Music transport controls (Apple Music style): shuffle / previous / next
            controls_frame = _tk.Frame(content, bg='#252525')
            controls_frame.pack(fill='x', pady=(0, 8))
            shuffle_cb = _tk.Checkbutton(
                controls_frame,
                text="Shuffle",
                variable=self.music_shuffle_var,
                bg='#252525',
                fg='#FFFFFF',
                selectcolor='#1a1a1a',
                activebackground='#252525',
                activeforeground='#FFFFFF',
                font=("Segoe UI", 10),
                relief='flat',
                cursor='hand2'
            )
            shuffle_cb.pack(side='left')
            transport_frame = _tk.Frame(controls_frame, bg='#252525')
            transport_frame.pack(side='right')
            # Placeholder callback; rebound after now-playing canvas is created.
            _refresh_now_playing_canvas = lambda: None
            prev_btn = _tk.Button(
                transport_frame, text="⏮", command=lambda: (self._play_previous_track(show_popup=True, popup_force=True), _refresh_now_playing_canvas()),
                bg='#3a3a3a', fg='#FFFFFF', font=("Segoe UI", 11), relief='flat', cursor='hand2',
                activebackground='#9333ea', activeforeground='#FFFFFF', padx=10, pady=3
            )
            prev_btn.pack(side='left', padx=(0, 6))
            next_btn = _tk.Button(
                transport_frame, text="⏭", command=lambda: (self._play_next_track(show_popup=True, popup_force=True), _refresh_now_playing_canvas()),
                bg='#3a3a3a', fg='#FFFFFF', font=("Segoe UI", 11), relief='flat', cursor='hand2',
                activebackground='#9333ea', activeforeground='#FFFFFF', padx=10, pady=3
            )
            next_btn.pack(side='left')
            self._create_tooltip(shuffle_cb, "Shuffle playback order.")
            self._create_tooltip(prev_btn, "Play previous song.")
            self._create_tooltip(next_btn, "Play next song.")
            # Now playing (marquee for long names; cleaned title formatting)
            self._settings_marquee_after_id = None
            _np_canvas_w = content_width_custom
            _np_canvas_h = 18
            _np_font = _font.Font(family="Segoe UI", size=9)
            now_playing_canvas = _tk.Canvas(content, width=_np_canvas_w, height=_np_canvas_h, bg="#252525", highlightthickness=0)
            now_playing_canvas.pack(anchor="w", pady=(0, 14))
            def _render_now_playing_canvas():
                try:
                    if getattr(self, "_settings_marquee_after_id", None) is not None:
                        try:
                            self._root.after_cancel(self._settings_marquee_after_id)
                        except Exception:
                            pass
                        self._settings_marquee_after_id = None
                    if not now_playing_canvas.winfo_exists():
                        return
                    now_playing_canvas.delete("all")
                    _now_playing = self._format_track_display_name(getattr(self, "_current_track_name", None))
                    if _now_playing and _now_playing != "Unknown":
                        _np_text = "Now playing: " + _now_playing
                        _np_text_width = _np_font.measure(_np_text)
                        if _np_text_width <= _np_canvas_w - 4:
                            now_playing_canvas.create_text(2, _np_canvas_h // 2, text=_np_text, fill="#9ca3af", font=("Segoe UI", 9), anchor="w")
                        else:
                            _gap = "     "
                            _np_loop_text = _np_text + _gap + _np_text
                            _reset_at = _np_font.measure(_np_text + _gap)
                            _np_tid = now_playing_canvas.create_text(2, _np_canvas_h // 2, text=_np_loop_text, fill="#9ca3af", font=("Segoe UI", 9), anchor="w")
                            _np_x = [2]
                            _NP_MS = 28
                            _NP_STEP = 1
                            def _settings_marquee_step():
                                if not getattr(self, "_settings_dropdown", None) or not self._settings_dropdown.winfo_exists():
                                    return
                                try:
                                    if not now_playing_canvas.winfo_exists():
                                        return
                                    now_playing_canvas.coords(_np_tid, _np_x[0], _np_canvas_h // 2)
                                    _np_x[0] -= _NP_STEP
                                    if _np_x[0] <= -_reset_at:
                                        _np_x[0] = 2
                                    self._settings_marquee_after_id = self._root.after(_NP_MS, _settings_marquee_step)
                                except Exception:
                                    pass
                            self._settings_marquee_after_id = self._root.after(450, _settings_marquee_step)
                            self._create_tooltip(now_playing_canvas, _np_text)
                    else:
                        now_playing_canvas.create_text(_np_canvas_w // 2, _np_canvas_h // 2, text="Nothing playing", fill="#9ca3af", font=("Segoe UI", 9), anchor="center")
                except Exception:
                    pass
            _refresh_now_playing_canvas = _render_now_playing_canvas
            self._settings_refresh_now_playing = _refresh_now_playing_canvas
            _render_now_playing_canvas()
            self._create_tooltip(music_vol_scale, "Background music volume (0-100%). Applied immediately." if _("settings.music_volume_tooltip") == "settings.music_volume_tooltip" else _("settings.music_volume_tooltip"))
            
            _tk.Frame(content, bg='#404040', height=2).pack(fill='x', pady=(0, 12))

            # ---- Section: Auto-Import to Minecraft Bedrock ----
            _ai_cw = menu_width - 4 - 32
            ai_label = _tk.Label(content, text="🎮 Auto-Import to Minecraft Bedrock", bg='#252525', fg='#E5E7EB',
                                 font=("Segoe UI", 11, "bold"), wraplength=_ai_cw, justify='left')
            ai_label.pack(anchor='w', pady=(0, 6))
            self._create_tooltip(ai_label, "After merging, automatically copy the merged packs into Minecraft Bedrock's com.mojang folder.")
            _ai_chk = _tk.Checkbutton(content, text="Auto-import after merge",
                                      variable=self._auto_import_var, bg='#252525', fg='#FFFFFF',
                                      selectcolor='#1a1a1a', activebackground='#252525', activeforeground='#FFFFFF',
                                      font=("Segoe UI", 10), relief='flat', cursor='hand2')
            _ai_chk.pack(anchor='w', pady=(0, 8))
            _ai_path_frame = _tk.Frame(content, bg='#252525')
            _ai_path_frame.pack(fill='x', pady=(0, 4))
            _ai_path_frame.columnconfigure(0, weight=1)
            _ai_enabled = self._auto_import_var.get()
            self._entry_mc_path = _tk.Entry(
                _ai_path_frame, textvariable=self._mc_path_var,
                bg='#1a1a1a', fg='#FFFFFF' if _ai_enabled else '#888888',
                font=("Segoe UI", 9), insertbackground='#a855f7',
                relief='flat', highlightthickness=1, highlightbackground='#3a3a3a',
                highlightcolor='#9333ea', state='normal' if _ai_enabled else 'disabled')
            self._entry_mc_path.grid(row=0, column=0, padx=(0, 6), sticky='ew', ipady=5)
            self._btn_mc_browse = _tk.Button(
                _ai_path_frame, text="Browse", command=self._browse_mc_path,
                bg='#9333ea' if _ai_enabled else '#374151',
                fg='#FFFFFF' if _ai_enabled else '#888888',
                font=("Segoe UI", 9, "bold"), relief='flat', cursor='hand2',
                activebackground='#a855f7', state='normal' if _ai_enabled else 'disabled')
            self._btn_mc_browse.grid(row=0, column=1, sticky='ew')
            _ai_chk.config(command=self._toggle_mc_import_path)

            _tk.Frame(content, bg='#404040', height=2).pack(fill='x', pady=(12, 12))

            # ---- Section 3: Check for updates ----
            update_btn = _tk.Button(content, text=_("settings.check_for_updates"), command=self._check_for_updates,
                                   bg='#3a3a3a', fg='#FFFFFF', font=("Segoe UI", 11), relief='flat', cursor='hand2',
                                   activebackground='#9333ea', activeforeground='#FFFFFF', padx=14, pady=12, anchor='w')
            update_btn.pack(fill='x', pady=(0, 0))
            
            # Close dropdown when clicking outside.
            # Use screen bounding-box test — reliable even inside canvas create_window.
            def close_on_click(event):
                try:
                    if not hasattr(self, "_settings_dropdown") or not self._settings_dropdown.winfo_exists():
                        return
                    # Suppress during file dialogs or other blocking calls
                    if getattr(self, '_suppress_settings_close', False):
                        return
                    # Bounding-box test in screen coordinates
                    try:
                        _dx = self._settings_dropdown.winfo_rootx()
                        _dy = self._settings_dropdown.winfo_rooty()
                        _dw = self._settings_dropdown.winfo_width()
                        _dh = self._settings_dropdown.winfo_height()
                        if _dx <= event.x_root <= _dx + _dw and _dy <= event.y_root <= _dy + _dh:
                            return  # click was inside dropdown area
                    except Exception:
                        pass
                    # Also skip notebook tab bar clicks (re-toggle)
                    try:
                        if event.widget == self.notebook:
                            return
                    except Exception:
                        pass
                    self._close_settings_dropdown()
                except Exception:
                    pass
            
            self._root.bind('<Button-1>', close_on_click, add='+')
            
            # Clean up on dropdown destroy
            def on_dropdown_destroy(event=None):
                self._close_settings_dropdown()
            
            self._settings_dropdown.bind('<Destroy>', on_dropdown_destroy)
        except Exception as e:
            log_error(f"Error showing settings dropdown: {e}")
            import traceback
            log_error(traceback.format_exc())

    def init_mcpacker_tab(self):
        # Configure mcpacker_frame for proper resizing (will be set after all widgets are created)
        
        # LabelFrame for selecting input files - Modern styling
        self._frame_mcpacker_files = _tk.LabelFrame(self.mcpacker_frame, text="📦 " + _("mcpacker.select_files"), bg='#1a1a1a', fg='#FFFFFF', font=("Segoe UI", 13, "bold"))
        self._frame_mcpacker_files.grid(row=0, column=0, padx=15, pady=(15, 10), sticky="nsew")

        self._mcpacker_file_list_data = []
        self._mcpacker_file_list_photo_refs = []
        self._mcpacker_file_list_selected = set()
        self._mcpacker_file_paths = {}
        self._mcpacker_files = []

        listbox_frame = _tk.Frame(self._frame_mcpacker_files, bg='#1a1a1a')
        listbox_frame.grid(row=0, column=0, padx=12, pady=(8, 6), sticky="nsew")
        listbox_frame.grid_columnconfigure(0, weight=1)
        listbox_frame.grid_rowconfigure(0, weight=1)
        self._mcpacker_file_list_canvas = _tk.Canvas(listbox_frame, bg='#0A0A0A', highlightthickness=0, yscrollincrement=40)
        self._mcpacker_file_list_canvas.grid(row=0, column=0, sticky="nsew")
        self._mcpacker_file_list_inner = _tk.Frame(self._mcpacker_file_list_canvas, bg='#0A0A0A')
        self._mcpacker_file_list_canvas_window = self._mcpacker_file_list_canvas.create_window(0, 0, window=self._mcpacker_file_list_inner, anchor='nw')
        def _on_mcpacker_list_configure(event):
            self._mcpacker_file_list_canvas.configure(scrollregion=self._mcpacker_file_list_canvas.bbox('all'))
            self._mcpacker_file_list_canvas.itemconfig(self._mcpacker_file_list_canvas_window, width=event.width)
        self._mcpacker_file_list_inner.bind('<Configure>', _on_mcpacker_list_configure)
        self._mcpacker_file_list_canvas.bind('<Configure>', lambda e: self._mcpacker_file_list_canvas.itemconfig(self._mcpacker_file_list_canvas_window, width=e.width))
        def _mcpacker_wheel(e):
            if getattr(e, 'num', None) == 4:
                self._mcpacker_file_list_canvas.yview_scroll(-3, 'units')
            elif getattr(e, 'num', None) == 5:
                self._mcpacker_file_list_canvas.yview_scroll(3, 'units')
            else:
                delta = getattr(e, 'delta', 0)
                units = max(1, abs(delta) // 40) * (-1 if delta > 0 else 1)
                self._mcpacker_file_list_canvas.yview_scroll(units, 'units')
        # Store so _rebuild_mcpacker_file_list can propagate to every row/label
        self._mcpacker_wheel_handler = _mcpacker_wheel
        for _ev in ('<MouseWheel>', '<Button-4>', '<Button-5>'):
            self._mcpacker_file_list_canvas.bind(_ev, _mcpacker_wheel)
            self._mcpacker_file_list_inner.bind(_ev, _mcpacker_wheel)

        # File count label + Select All button row
        _mp_count_row = _tk.Frame(self._frame_mcpacker_files, bg='#1a1a1a')
        _mp_count_row.grid(row=1, column=0, padx=12, pady=(0, 6), sticky="ew")
        _mp_count_row.grid_columnconfigure(0, weight=1)
        self._mcpacker_file_count_label = _tk.Label(_mp_count_row, text=_f("app.files_selected", n=0), bg='#1a1a1a', fg='#FFFFFF', font=("Segoe UI", 10))
        self._mcpacker_file_count_label.grid(row=0, column=0, sticky="w")
        self._mcpacker_btn_select_all = _tk.Button(_mp_count_row, text="Select All", command=self._toggle_select_all_mcpacker,
            bg='#2d2d2d', fg='#CCCCCC', font=("Segoe UI", 9), relief='flat', cursor='hand2',
            activebackground='#3d3d3d', activeforeground='#FFFFFF', padx=10, pady=2)
        self._mcpacker_btn_select_all.grid(row=0, column=1, sticky="e")
        self._mcpacker_btn_select_all.grid_remove()  # hidden until files are added

        # Button container for better alignment
        button_container = _tk.Frame(self._frame_mcpacker_files, bg='#1a1a1a')
        button_container.grid(row=2, column=0, padx=12, pady=(0, 8), sticky="ew")
        button_container.grid_columnconfigure(0, weight=1)
        button_container.grid_columnconfigure(1, weight=1)
        
        # Browse Button for selecting files - Modern styling
        self._btn_mcpacker_browse_files = _tk.Button(button_container, text="➕ " + _("app.add_files"), command=self.select_files, bg='#9333ea', fg='#FFFFFF', font=("Segoe UI", 11, "bold"), relief='flat', cursor='hand2', activebackground='#a855f7')
        self._btn_mcpacker_browse_files.grid(row=0, column=0, padx=(0, 6), sticky="ew")
        
        # Remove Selected Button - Modern styling
        self._btn_mcpacker_remove = _tk.Button(button_container, text="🗑️ " + _("app.remove_selected"), command=self.remove_mcpacker_files, bg='#1a1a1a', fg='#FFFFFF', font=("Segoe UI", 11), relief='flat', cursor='hand2', activebackground='#2d2d2d')
        self._btn_mcpacker_remove.grid(row=0, column=1, padx=(6, 0), sticky="ew")

        # Configure resizing for files frame
        self._frame_mcpacker_files.grid_columnconfigure(0, weight=1)
        self._frame_mcpacker_files.grid_rowconfigure(0, weight=1)  # Listbox frame - expandable
        self._frame_mcpacker_files.grid_rowconfigure(1, weight=0)  # File count - fixed
        self._frame_mcpacker_files.grid_rowconfigure(2, weight=0)  # Buttons - fixed

        # LabelFrame for output directory selection - Modern styling
        self._frame_mcpacker_output = _tk.LabelFrame(self.mcpacker_frame, text="📂 " + _("app.select_output_dir"), bg='#1a1a1a', fg='#FFFFFF', font=("Segoe UI", 13, "bold"))
        self._frame_mcpacker_output.grid(row=1, column=0, padx=15, pady=(8, 8), sticky="nsew")

        self.output_dir_var = _tk.StringVar()

        # Output Directory Entry - Modern styling
        self._entry_mcpacker_output = _tk.Entry(self._frame_mcpacker_output, textvariable=self.output_dir_var, width=50, bg='#0A0A0A', fg='#FFFFFF', font=("Segoe UI", 11), insertbackground='#a855f7', relief='flat', highlightthickness=1, highlightbackground='#1a1a1a', highlightcolor='#9333ea')
        self._entry_mcpacker_output.grid(row=0, column=0, padx=12, pady=8, sticky="ew", ipady=6)
        # Browse Button for selecting output directory - Modern styling
        self._btn_mcpacker_browse_output = _tk.Button(self._frame_mcpacker_output, text=_("app.browse"), command=self.select_output_directory, bg='#9333ea', fg='#FFFFFF', font=("Segoe UI", 11, "bold"), relief='flat', cursor='hand2', activebackground='#a855f7')
        self._btn_mcpacker_browse_output.grid(row=0, column=1, padx=(0, 12), pady=8, sticky="ew")

        # Configure resizing for output frame
        self._frame_mcpacker_output.grid_columnconfigure(0, weight=1)

        # Progress Display Section - MCPACKER processing progress
        self._frame_mcpacker_progress = _tk.LabelFrame(self.mcpacker_frame, text="📊 " + _("app.processing_progress"), bg='#1a1a1a', fg='#FFFFFF', font=("Segoe UI", 13, "bold"))
        self._frame_mcpacker_progress.grid(row=2, column=0, padx=15, pady=(8, 8), sticky="nsew")
        self._frame_mcpacker_progress.columnconfigure(0, weight=1)
        self._frame_mcpacker_progress.grid_rowconfigure(0, weight=0)  # Progress container - fixed height
        
        progress_container = _tk.Frame(self._frame_mcpacker_progress, bg='#1a1a1a')
        progress_container.grid(row=0, column=0, padx=12, pady=(8, 8), sticky="nsew")
        progress_container.columnconfigure(0, weight=1)
        progress_container.rowconfigure(0, weight=0)  # Step label - fixed
        progress_container.rowconfigure(1, weight=0)  # Progress bar - fixed
        progress_container.rowconfigure(2, weight=0)  # Steps frame - fixed
        
        # Current step label
        self._mcpacker_progress_step_label = _tk.Label(progress_container, text=_("app.ready_to_process"), 
                                             bg='#1a1a1a', fg='#FFFFFF', 
                                             font=('Segoe UI', 11, 'bold'),
                                             anchor='center')
        self._mcpacker_progress_step_label.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        
        # Progress bar
        style = _ttk.Style()
        style.theme_use('clam')
        style.configure("MCPackerProgress.Horizontal.TProgressbar", background='#9333ea', troughcolor='#0A0A0A', borderwidth=0)
        self._mcpacker_progress = _ttk.Progressbar(progress_container, orient='horizontal', 
                                         length=400, mode='determinate', 
                                         style="MCPackerProgress.Horizontal.TProgressbar",
                                         maximum=100)
        self._mcpacker_progress.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        
        # Steps indicator (4 steps for MCPACKER)
        steps_frame = _tk.Frame(progress_container, bg='#1a1a1a')
        steps_frame.grid(row=2, column=0, sticky="ew", pady=(0, 0))
        steps_frame.grid_columnconfigure(0, weight=1)
        steps_frame.grid_columnconfigure(1, weight=1)
        steps_frame.grid_columnconfigure(2, weight=1)
        steps_frame.grid_columnconfigure(3, weight=1)
        
        self._mcpacker_step_labels = []
        # Step names will be updated based on mode (step 2 label switches to Extracting when in extract mode)
        step_names = [_("progress.reading_files"), _("progress.finding_packs"), _("progress.packaging_files"), _("progress.finalizing")]
        for i, step_name in enumerate(step_names):
            step_frame = _tk.Frame(steps_frame, bg='#1a1a1a')
            step_frame.grid(row=0, column=i, padx=3, sticky="")
            
            # Step number/status indicator
            step_status = _tk.Label(step_frame, text="○", bg='#1a1a1a', fg='#666666',
                                   font=('Segoe UI', 12), width=2, anchor='w')
            step_status.pack(side='left')
            self._mcpacker_step_labels.append({'status': step_status, 'name': step_name})
            
            # Step name
            step_label = _tk.Label(step_frame, text=step_name, bg='#1a1a1a', fg='#999999',
                                  font=('Segoe UI', 8))
            step_label.pack(side='left')
            self._mcpacker_step_labels[i]['label'] = step_label

        # Frame for the start button - Modern styling
        self._frame_mcpacker_controls = _tk.Frame(self.mcpacker_frame, bg='#000000')
        self._frame_mcpacker_controls.grid(row=3, column=0, padx=15, pady=(8, 8), sticky="ew")

        # Start Button for initiating the process - Modern styling
        self._btn_mcpacker_start = _tk.Button(self._frame_mcpacker_controls, text="🚀 " + _("mcpacker.start"), command=self.start_mcpacker, bg='#9333ea', fg='#FFFFFF', font=("Segoe UI", 12, "bold"), relief='flat', cursor='hand2', activebackground='#a855f7', padx=20, pady=10)
        self._btn_mcpacker_start.grid(row=0, column=0, padx=0, pady=0, sticky="ew")

        # Configure grid layout for controls
        self._frame_mcpacker_controls.grid_columnconfigure(0, weight=1)
        
        # Now configure mcpacker_frame for proper resizing after all widgets are created
        self.mcpacker_frame.grid_columnconfigure(0, weight=1)
        self.mcpacker_frame.grid_rowconfigure(0, weight=1, minsize=200)  # Files frame - expandable with minimum size
        self.mcpacker_frame.grid_rowconfigure(1, weight=0)  # Output frame - fixed
        self.mcpacker_frame.grid_rowconfigure(2, weight=0)  # Progress frame - fixed (don't shrink)
        self.mcpacker_frame.grid_rowconfigure(3, weight=0)  # Controls frame - fixed

    def init_list_maker_tab(self):
        # Frame for List Maker Tab - Modern styling
        self._frame_list_maker = _tk.LabelFrame(self.list_maker_frame, text="📋 " + _("list_maker.title"), bg='#1a1a1a', fg='#FFFFFF', font=("Segoe UI", 13, "bold"))
        self._frame_list_maker.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")

        # Mode Selection - Modern styling
        self.mode_var = _tk.StringVar(value="merged")
        self.mode_label = _tk.Label(self._frame_list_maker, text=_f("list_maker.mode", mode=_("list_maker.merged")), bg='#1a1a1a', fg='#FFFFFF', font=("Segoe UI", 12, "bold"))
        self.mode_label.grid(row=0, column=0, padx=12, pady=(12, 8), sticky="w")

        self._radio_merged = _tk.Radiobutton(self._frame_list_maker, text=_("list_maker.merged_list"), variable=self.mode_var, value="merged",
                        bg='#1a1a1a', fg='#FFFFFF', selectcolor='#9333ea', font=("Segoe UI", 11),
                        activebackground='#1a1a1a', activeforeground='#FFFFFF', command=self.update_mode_label)
        self._radio_merged.grid(row=1, column=0, padx=12, pady=5, sticky="w")
        
        self._radio_alone = _tk.Radiobutton(self._frame_list_maker, text=_("list_maker.alone_list"), variable=self.mode_var, value="alone",
                        bg='#1a1a1a', fg='#FFFFFF', selectcolor='#9333ea', font=("Segoe UI", 11),
                        activebackground='#1a1a1a', activeforeground='#FFFFFF', command=self.update_mode_label)
        self._radio_alone.grid(row=2, column=0, padx=12, pady=5, sticky="w")

        # Add Files Button - Modern styling
        self._btn_add_files = _tk.Button(self._frame_list_maker, text="➕ " + _("list_maker.add_files"), command=self.on_add_files,
                                         bg='#9333ea', fg='#FFFFFF', font=("Segoe UI", 11, "bold"), relief='flat', cursor='hand2', activebackground='#a855f7')
        self._btn_add_files.grid(row=3, column=0, padx=12, pady=12, sticky="ew")

        # File list with pack icon + name (scrollable)
        self._list_maker_photo_refs = []
        list_maker_list_frame = _tk.Frame(self._frame_list_maker, bg='#1a1a1a')
        list_maker_list_frame.grid(row=4, column=0, padx=12, pady=12, sticky="nsew")
        list_maker_list_frame.grid_columnconfigure(0, weight=1)
        list_maker_list_frame.grid_rowconfigure(0, weight=1)
        self._list_maker_canvas = _tk.Canvas(list_maker_list_frame, bg='#0A0A0A', highlightthickness=0)
        self._list_maker_canvas.grid(row=0, column=0, sticky="nsew")
        self._list_maker_inner = _tk.Frame(self._list_maker_canvas, bg='#0A0A0A')
        self._list_maker_canvas_window = self._list_maker_canvas.create_window(0, 0, window=self._list_maker_inner, anchor='nw')
        self._list_maker_inner.bind('<Configure>', lambda e: (self._list_maker_canvas.configure(scrollregion=self._list_maker_canvas.bbox('all')), self._list_maker_canvas.itemconfig(self._list_maker_canvas_window, width=e.width)))
        self._list_maker_canvas.bind('<Configure>', lambda e: self._list_maker_canvas.itemconfig(self._list_maker_canvas_window, width=e.width))
        def _list_maker_wheel(e):
            self._list_maker_canvas.yview_scroll(int(-1 * (e.delta / 120)), 'units')
        def _list_maker_scroll_enter(e):
            self._list_maker_canvas.bind_all('<MouseWheel>', _list_maker_wheel)
        def _list_maker_scroll_leave(e):
            try:
                self._list_maker_canvas.unbind_all('<MouseWheel>')
            except Exception:
                pass
        self._list_maker_canvas.bind('<Enter>', _list_maker_scroll_enter)
        self._list_maker_canvas.bind('<Leave>', _list_maker_scroll_leave)
        self._list_maker_inner.bind('<Enter>', _list_maker_scroll_enter)
        self._list_maker_inner.bind('<Leave>', _list_maker_scroll_leave)

        # Export List Button - Modern styling
        self._btn_export_list = _tk.Button(self._frame_list_maker, text="💾 " + _("list_maker.export_list"), command=self.export_list,
                                           bg='#9333ea', fg='#FFFFFF', font=("Segoe UI", 11, "bold"), relief='flat', cursor='hand2', activebackground='#a855f7')
        self._btn_export_list.grid(row=5, column=0, padx=12, pady=12, sticky="ew")

        # Configure resizing for List Maker frame
        self._frame_list_maker.grid_columnconfigure(0, weight=1)
        self._frame_list_maker.grid_rowconfigure(4, weight=1)

    def update_mode_label(self):
        mode_key = "list_maker.merged" if self.mode_var.get() == "merged" else "list_maker.alone"
        self.mode_label.config(text=_f("list_maker.mode", mode=_(mode_key)))

    def on_add_files(self):
        files = _filedialog.askopenfilenames(
            title=_("filedialog.select_mcpacks"),
            filetypes=[("MCPack Files", "*.mcpack")]
        )
        self.selected_files = list(files)
        self.update_file_list()

    def update_file_list(self):
        for w in self._list_maker_inner.winfo_children():
            w.destroy()
        self._list_maker_photo_refs.clear()
        for file_path in self.selected_files:
            display_name, photo, full_photo = self._get_pack_display_info(file_path)
            row = _tk.Frame(self._list_maker_inner, bg='#0A0A0A', height=52)
            row.pack(fill='x', padx=4, pady=2)
            row.pack_propagate(False)
            if photo:
                self._list_maker_photo_refs.append(photo)
                if full_photo:
                    self._list_maker_photo_refs.append(full_photo)
                icon_lbl = _tk.Label(row, image=photo, bg='#0A0A0A')
            else:
                icon_lbl = _tk.Label(row, text='\u26fa', font=('Segoe UI', 20), bg='#0A0A0A', fg='#666666')
            icon_lbl.pack(side=_tk.LEFT, padx=(8, 10), pady=6)
            name_lbl = _tk.Label(row, text=display_name, bg='#0A0A0A', fg='#FFFFFF', font=('Segoe UI', 10), anchor='w')
            name_lbl.pack(side=_tk.LEFT, fill='x', expand=True, pady=6)
        self._list_maker_canvas.configure(scrollregion=self._list_maker_canvas.bbox('all'))

    def clean_file_name(self, file_name):
        cleaned_name = _re.sub(r"_", " ", file_name)
        cleaned_name = _re.sub(r"\d+", "", cleaned_name)
        cleaned_name = _re.sub(r"\.mcpack", "", cleaned_name)
        return cleaned_name.strip()

    def export_list(self):
        if not self.selected_files:
            _messagebox.showwarning("No Files Selected", "Please select MCPack files to export.")
            return

        mode = self.mode_var.get()
        self.organize_and_export(self.selected_files, mode)
