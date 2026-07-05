class AutoBEApp:
    def __init__(self, _root):
        self._root = _root
        self._pending_update_result = _consume_post_update_result_arg()
        self._is_maximized = False
        self._restore_geometry = None
        self._drag_offset_x = 0
        self._drag_offset_y = 0
        # Register AppUserModelID before any window draws so the taskbar
        # button gets its own slot with the correct icon from the start.
        _set_app_user_model_id()
        if platform.system() == "Windows" and not getattr(sys, "frozen", False):
            for _ms in (50, 150, 350, 600, 1000):
                self._root.after(_ms, _hide_console_window)
        self._root.title("AutoBE - CodeNex")
        self._apply_window_icon(self._root)
        self._root.geometry("900x800")
        self._root.minsize(900, 800)
        # Modern dark theme background - pure black for activation window
        self._root.configure(bg='#000000')
        # Use custom title bar so we never show white native caption.
        self._root.overrideredirect(True)
        # Hide main window initially - will be shown after terms are accepted
        self._root.withdraw()
        # Don't apply taskbar fixes - they cause flickering with withdraw/deiconify
        # Taskbar button will appear naturally when window is shown

        # Allow the main window to be resized
        self._root.columnconfigure(0, weight=1)
        self._root.rowconfigure(0, weight=0)  # custom title bar
        self._root.rowconfigure(1, weight=1)  # app content
        self._init_custom_title_bar()

        # Create activation overlay frame (shown first, covers everything)
        self._activation_overlay = _tk.Frame(self._root, bg='#000000')
        self._activation_overlay.grid(row=1, column=0, sticky="nsew")
        self._activation_overlay.columnconfigure(0, weight=1)
        self._activation_overlay.rowconfigure(0, weight=1)
        
        # Create subpack selection overlay frame (hidden by default)
        self._subpack_overlay = _tk.Frame(self._root, bg='#0f1419')
        self._subpack_overlay.grid(row=1, column=0, sticky="nsew")
        self._subpack_overlay.columnconfigure(0, weight=1)
        self._subpack_overlay.rowconfigure(0, weight=1)
        self._subpack_overlay.grid_remove()  # Hide initially
        
        # Create version check overlay frame (hidden by default)
        self._version_check_overlay = _tk.Frame(self._root, bg='#0f1419')
        self._version_check_overlay.grid(row=1, column=0, sticky="nsew")
        self._version_check_overlay.columnconfigure(0, weight=1)
        self._version_check_overlay.rowconfigure(0, weight=1)
        self._version_check_overlay.grid_remove()  # Hide initially
        
        # Create ban screen overlay frame (hidden by default)
        self._ban_overlay = _tk.Frame(self._root, bg='#000000')
        self._ban_overlay.grid(row=1, column=0, sticky="nsew")
        self._ban_overlay.columnconfigure(0, weight=1)
        self._ban_overlay.rowconfigure(0, weight=1)
        self._ban_overlay.grid_remove()  # Hide initially
        
        # Create achievement status overlay frame (hidden by default)
        self._achievement_overlay = _tk.Frame(self._root, bg='#0f1419')
        self._achievement_overlay.grid(row=1, column=0, sticky="nsew")
        self._achievement_overlay.columnconfigure(0, weight=1)
        self._achievement_overlay.rowconfigure(0, weight=1)
        self._achievement_overlay.grid_remove()  # Hide initially
        
        # Create script API check overlay (Check Packs - script dependency grouping)
        self._script_api_overlay = _tk.Frame(self._root, bg='#0f1419')
        self._script_api_overlay.grid(row=1, column=0, sticky="nsew")
        self._script_api_overlay.columnconfigure(0, weight=1)
        self._script_api_overlay.rowconfigure(0, weight=1)
        self._script_api_overlay.grid_remove()  # Hide initially

        # Create identifier conflict resolution overlay (merge: choose which pack to keep per conflict)
        self._conflict_resolution_overlay = _tk.Frame(self._root, bg='#0f1419')
        self._conflict_resolution_overlay.grid(row=1, column=0, sticky="nsew")
        self._conflict_resolution_overlay.columnconfigure(0, weight=1)
        self._conflict_resolution_overlay.rowconfigure(0, weight=1)
        self._conflict_resolution_overlay.grid_remove()  # Hide initially
        
        # Create update-in-progress overlay (themed, like verification loading)
        self._update_overlay = _tk.Frame(self._root, bg='#000000')
        self._update_overlay.grid(row=1, column=0, sticky="nsew")
        self._update_overlay.columnconfigure(0, weight=1)
        self._update_overlay.rowconfigure(0, weight=1)
        self._update_overlay.grid_remove()  # Hide initially
        self._update_check_lock = threading.Lock()
        
        # Create Notebook for Tabs (hidden until activation)
        self.notebook = _ttk.Notebook(self._root)
        self.notebook.grid(row=1, column=0, sticky="nsew")
        self.notebook.grid_remove()  # Hide initially
        
        # Style the notebook tabs - pitch black, transparent look
        style = _ttk.Style()
        style.theme_use('clam')
        style.configure('TNotebook', background='#000000', borderwidth=0)
        style.configure('TNotebook.Tab', background='#000000', foreground='#888888', padding=[20, 10], borderwidth=0)
        style.map('TNotebook.Tab', background=[('selected', '#9333ea')], foreground=[('selected', '#FFFFFF')])

        # Create Frames for each Tab - pitch black background
        self.app1_frame = _tk.Frame(self.notebook, bg='#000000')
        self.mcpacker_frame = _tk.Frame(self.notebook, bg='#000000')
        self.list_maker_frame = _tk.Frame(self.notebook, bg='#000000')  # New List Maker Tab
        self.settings_frame = _tk.Frame(self.notebook, bg='#000000')
        self.help_frame = _tk.Frame(self.notebook, bg='#000000')

        # Adding Tabs to Notebook
        self.notebook.add(self.app1_frame, text=_("tabs.autobe"))
        self.notebook.add(self.mcpacker_frame, text=_("tabs.mcpacker"))
        self.notebook.add(self.list_maker_frame, text=_("tabs.list_maker"))
        self.notebook.add(self.help_frame, text=_("tabs.help"))
        
        # Add Settings as a special tab that shows dropdown instead of content
        self.notebook.add(self.settings_frame, text=_("tabs.settings"))
        
        # Bind to intercept Settings tab clicks BEFORE tab changes
        self.notebook.bind("<Button-1>", self._on_notebook_click)
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        # Configure resizing for the notebook's frames
        for frame in [self.app1_frame, self.mcpacker_frame, self.list_maker_frame, self.settings_frame, self.help_frame]:
            frame.columnconfigure(0, weight=1)
            frame.rowconfigure(0, weight=1)

        # Load settings and initialize mode selection variable
        loaded_settings = self._load_settings()
        self._current_lang = loaded_settings.get("lang", "en")
        self.mcpacker_mode_var = _tk.StringVar(value=loaded_settings.get("mcpacker_mode", "pack"))
        self.merge_by_version_var = _tk.BooleanVar(value=loaded_settings.get("merge_by_version", False))
        self.customize_pack_after_merge_var = _tk.BooleanVar(value=loaded_settings.get("customize_pack_after_merge", False))
        self.show_linked_packs_after_merge_var = _tk.BooleanVar(value=loaded_settings.get("show_linked_packs_after_merge", False))
        self.extendedbe_enabled_var = _tk.BooleanVar(value=loaded_settings.get("extendedbe_enabled", False))
        self.modpack_organization_var = _tk.BooleanVar(value=loaded_settings.get("modpack_organization", False))
        self.background_music_var = _tk.BooleanVar(value=loaded_settings.get("background_music", True))
        self.background_music_volume_var = _tk.IntVar(value=min(100, max(0, loaded_settings.get("background_music_volume", 70))))
        self.music_shuffle_var = _tk.BooleanVar(value=loaded_settings.get("music_shuffle", True))
        self.music_playlist_var = _tk.StringVar(value=loaded_settings.get("music_playlist", "__all__"))
        
        # Add trace to save settings whenever the variable changes
        self.mcpacker_mode_var.trace_add('write', lambda *args: self._save_settings())
        self.merge_by_version_var.trace_add('write', lambda *args: self._save_settings())
        self.customize_pack_after_merge_var.trace_add('write', lambda *args: self._save_settings())
        self.show_linked_packs_after_merge_var.trace_add('write', lambda *args: self._save_settings())
        self.extendedbe_enabled_var.trace_add('write', lambda *args: self._save_settings())
        self.modpack_organization_var.trace_add('write', lambda *args: self._save_settings())
        def _on_background_music_var_change(*args):
            self._save_settings()
            if getattr(self, '_root', None) and self._root.winfo_exists():
                self._root.after(0, self._apply_background_music_setting)
        self.background_music_var.trace_add('write', _on_background_music_var_change)
        def _on_background_music_volume_change(*args):
            self._save_settings()
            if getattr(self, '_root', None) and self._root.winfo_exists():
                self._root.after(0, self._apply_background_music_volume)
            try:
                lbl = getattr(self, "_settings_vol_value_label", None)
                if lbl is not None and lbl.winfo_exists():
                    lbl.config(text=str(getattr(self, "background_music_volume_var", _tk.IntVar(value=70)).get()) + "%")
            except Exception:
                pass
        self.background_music_volume_var.trace_add('write', _on_background_music_volume_change)
        def _on_music_shuffle_var_change(*args):
            self._save_settings()
            self._on_music_shuffle_setting_changed()
        self.music_shuffle_var.trace_add('write', _on_music_shuffle_var_change)
        def _on_music_playlist_var_change(*args):
            self._save_settings()
            self._on_music_playlist_setting_changed()
        self.music_playlist_var.trace_add('write', _on_music_playlist_var_change)

        # Initialize Settings Tab first (so mode is available for MCPACKER)
        self.init_settings_tab()

        # Initialize MCPACKER Tab Content
        self.init_mcpacker_tab()

        # Initialize List Maker Tab Content
        self.init_list_maker_tab()

        # Initialize Help Tab Content
        self.init_help_tab()
        
        # Track loading state for close protection
        self._is_loading = False
        
        # Initialize Discord Rich Presence (optional) — deferred, then run in thread so pipe tries don't freeze UI
        self.discord_rpc = None
        self._root.after(500, lambda: threading.Thread(target=self._init_discord_rpc, daemon=True).start())
        
        # Bind tab change event - handled by _on_settings_tab_click which also calls _on_tab_changed
        # _on_settings_tab_click will handle Settings tab specially
        
        # Set up window close protocol handler
        self._original_protocol = None
        self._root.protocol("WM_DELETE_WINDOW", self._on_window_close)
        
        # Defer activation until UI is ready to avoid root destruction errors
        self._root.after(0, self._check_activation)

    def _find_app_icon_paths(self):
        """Return candidate icon paths in priority order."""
        return _get_app_icon_paths()

    def _apply_window_icon(self, window):
        """Apply branded app icon to a Tk/Toplevel window."""
        _apply_window_icon_global(window)

    def _init_custom_title_bar(self):
        """Create dark custom title bar with drag/min/max/close controls."""
        self._titlebar = _tk.Frame(self._root, bg="#000000", height=34, highlightthickness=1, highlightbackground="#1f1f1f")
        self._titlebar.grid(row=0, column=0, sticky="ew")
        self._titlebar.grid_columnconfigure(1, weight=1)
        self._titlebar.grid_propagate(False)

        self._main_title_icon_img = _get_titlebar_icon_image(14)
        if self._main_title_icon_img is not None:
            title_icon = _tk.Label(self._titlebar, image=self._main_title_icon_img, bg="#000000")
        else:
            title_icon = _tk.Label(self._titlebar, text="◈", bg="#000000", fg="#9333ea", font=("Segoe UI", 10, "bold"))
        title_icon.grid(row=0, column=0, padx=(8, 6), sticky="w")
        self._title_text = _tk.Label(self._titlebar, text="AutoBE - CodeNex", bg="#000000", fg="#E5E7EB", font=("Segoe UI", 10))
        self._title_text.grid(row=0, column=1, sticky="w")

        btns = _tk.Frame(self._titlebar, bg="#000000")
        btns.grid(row=0, column=2, sticky="e")

        self._btn_min = _tk.Button(btns, text="—", command=self._window_minimize, bg="#000000", fg="#E5E7EB",
                                   font=("Segoe UI", 10, "bold"), relief="flat", bd=0, padx=12, pady=3,
                                   activebackground="#1f1f1f", activeforeground="#FFFFFF", cursor="hand2")
        self._btn_min.pack(side="left")
        self._btn_max = _tk.Button(btns, text="□", command=self._window_toggle_maximize, bg="#000000", fg="#E5E7EB",
                                   font=("Segoe UI", 10, "bold"), relief="flat", bd=0, padx=12, pady=3,
                                   activebackground="#1f1f1f", activeforeground="#FFFFFF", cursor="hand2")
        self._btn_max.pack(side="left")
        self._btn_close = _tk.Button(btns, text="✕", command=self._window_close, bg="#000000", fg="#E5E7EB",
                                     font=("Segoe UI", 10, "bold"), relief="flat", bd=0, padx=12, pady=3,
                                     activebackground="#c42b1c", activeforeground="#FFFFFF", cursor="hand2")
        self._btn_close.pack(side="left")

        for w in (self._titlebar, title_icon, self._title_text):
            w.bind("<ButtonPress-1>", self._window_drag_start, add="+")
            w.bind("<B1-Motion>", self._window_drag_move, add="+")
            w.bind("<Double-Button-1>", lambda e: self._window_toggle_maximize(), add="+")

        # Re-apply borderless mode after minimize/restore.
        self._root.bind("<Map>", self._window_on_map, add="+")

    def _window_drag_start(self, event):
        if self._is_maximized:
            return
        self._drag_offset_x = event.x_root - self._root.winfo_x()
        self._drag_offset_y = event.y_root - self._root.winfo_y()

    def _window_drag_move(self, event):
        if self._is_maximized:
            return
        x = event.x_root - self._drag_offset_x
        y = event.y_root - self._drag_offset_y
        self._root.geometry(f"+{x}+{y}")

    def _window_toggle_maximize(self):
        try:
            if not self._is_maximized:
                self._restore_geometry = self._root.geometry()
                sw = self._root.winfo_screenwidth()
                sh = self._root.winfo_screenheight()
                self._root.geometry(f"{sw}x{sh}+0+0")
                self._is_maximized = True
                self._btn_max.config(text="❐")
            else:
                if self._restore_geometry:
                    self._root.geometry(self._restore_geometry)
                self._is_maximized = False
                self._btn_max.config(text="□")
        except Exception:
            pass

    def _window_minimize(self):
        try:
            self._root.overrideredirect(False)
            self._root.iconify()
        except Exception:
            pass

    def _window_on_map(self, event=None):
        try:
            if self._root.state() != "iconic":
                self._root.overrideredirect(True)
        except Exception:
            pass

    def _window_close(self):
        try:
            self._on_window_close()
        except Exception:
            try:
                self._root.destroy()
            except Exception:
                pass

    def _init_discord_rpc(self):
        """Initialize Discord Rich Presence. Tries pipes 0-9; fails silently if Discord not running or pypresence missing."""
        if not getattr(self, "_root", None) or not self._root.winfo_exists():
            return
        self.discord_rpc = None
        presence_cls = Presence
        if presence_cls is None and getattr(sys, "frozen", False):
            try:
                from pypresence import Presence as _P  # type: ignore[import-untyped]
                presence_cls = _P
            except Exception:
                presence_cls = None
        if not DISCORD_RPC_AVAILABLE and presence_cls is None:
            return
        if presence_cls is None:
            return
        CLIENT_ID = "1304230074513358929"
        last_err = None
        for pipe in range(10):
            try:
                try:
                    rpc = presence_cls(CLIENT_ID, pipe=pipe, instance=False)
                except TypeError:
                    rpc = presence_cls(CLIENT_ID, instance=False)
                if not hasattr(rpc, "connect"):
                    continue
                rpc.connect()
                # First update must be on same thread as connect (some Discord clients drop it otherwise)
                try:
                    rpc.update(
                        details="Using AutoBE",
                        state="Ready • © CodeNex 2024",
                        large_image="autobediscord",
                        large_text="AutoBE - CodeNex",
                        start=int(_datetime.datetime.now().timestamp())
                    )
                except Exception:
                    try:
                        rpc.update(details="Using AutoBE", state="Ready • © CodeNex 2024")
                    except Exception:
                        pass
                self.discord_rpc = rpc
                # Schedule periodic refresh so Discord keeps showing presence (stops dropping after idle)
                if self._is_root_alive():
                    self._schedule_discord_refresh()
                return
            except Exception as e:
                last_err = e
                continue
        self.discord_rpc = None
        _logging.debug("Discord RPC failed (tried pipes 0-9): %s", last_err)
        _logging.info("Discord RPC unavailable (Discord may be closed): %s", last_err)

    # Rotating idle status pool — cycles every 45 s refresh
    _DISCORD_IDLE_POOL = [
        ("Building the ultimate modpack",      "In the lab"),
        ("Addon engineer on standby",           "Waiting to merge"),
        ("Making Bedrock hit different",        "AutoBE loaded & ready"),
        ("100+ addons? No problem",             "Merge wizard online"),
        ("Deep in the modpack trenches",         "Precision mode"),
        ("The modpack won't build itself",      "Get to work"),
        ("Every addon. One pack.",              "That's the AutoBE way"),
        ("Pushing Bedrock to its limits",       "Next-gen tooling"),
        ("Merge, deploy, repeat",               "Powered by CodeNex"),
        ("Crafting something legendary",        "Stay tuned"),
        ("Stress-testing 118 addons",           "Still not breaking a sweat"),
        ("Constructing the impossible pack",    "Brick by brick"),
        ("Packs sorted. Conflicts resolved.",   "AutoBE in session"),
        ("Bedrock edition, elevated",           "CodeNex ecosystem"),
        ("Future of Bedrock modding",           "You're early"),
    ]

    def _schedule_discord_refresh(self):
        """Re-send presence every 45s so Discord doesn't drop it. Cancelled on close."""
        if not getattr(self, "_root", None) or not self._root.winfo_exists():
            return
        # If Discord RPC failed to initialize, retry every 30 seconds
        if not self.discord_rpc:
            if getattr(self, "_root", None) and self._root.winfo_exists():
                self._discord_refresh_id = self._root.after(30000, self._schedule_discord_refresh)
                # Try to initialize Discord RPC again
                threading.Thread(target=self._init_discord_rpc, daemon=True).start()
            return
        # Don't stomp live merge status with idle rotating messages
        if not getattr(self, "_discord_merging", False):
            try:
                self._discord_idle_index = (getattr(self, "_discord_idle_index", -1) + 1) % len(self._DISCORD_IDLE_POOL)
                self._update_discord_presence()
            except Exception:
                self._update_discord_presence()
        if getattr(self, "_root", None) and self._root.winfo_exists():
            self._discord_refresh_id = self._root.after(45000, self._schedule_discord_refresh)

    def _set_discord_merge_step(self, details, state):
        """Immediately push a merge-step status to Discord (no self-imposed rate limit)."""
        if not self.discord_rpc or not hasattr(self.discord_rpc, "update"):
            return
        state_str = f"{state} \u2022 \u00a9 CodeNex 2025"
        try:
            self.discord_rpc.update(
                details=details,
                state=state_str,
                large_image="autobediscord",
                large_text="AutoBE by CodeNex",
                start=getattr(self, "_merge_discord_start", int(_datetime.datetime.now().timestamp()))
            )
        except Exception:
            try:
                self.discord_rpc.update(details=details, state=state_str)
            except Exception:
                pass
    
    def _update_discord_presence(self, details=None, state=None, tab_name=None):
        """Update Discord Rich Presence status. No-op if RPC is unavailable or update fails."""
        if not self.discord_rpc or not hasattr(self.discord_rpc, "update"):
            return
        try:
            # Check if Minecraft is running
            minecraft_running = self._is_minecraft_running()
            
            if details is None and state is None and tab_name is None:
                # Rotating idle pool — pick current index set by _schedule_discord_refresh
                idx = getattr(self, "_discord_idle_index", 0) % len(self._DISCORD_IDLE_POOL)
                details, state = self._DISCORD_IDLE_POOL[idx]
            elif tab_name:
                _tab_map = {
                    "AutoBE":     ("AutoBE — Addon Forge",   "Building the modpack"),
                    "MCPACKER":   ("MCPACKER — Pack Tools",  "Converting formats"),
                    "List Maker": ("List Maker — Planning", "Creating pack lists"),
                    "Help":       ("AutoBE — Documentation", "Learning the ropes"),
                }
                details, state = _tab_map.get(tab_name, ("AutoBE", "Idle"))
            
            # If Minecraft is running, show both activities
            if minecraft_running:
                if details and not details.startswith("Minecraft + "):
                    details = f"Minecraft + {details}"
                elif not details:
                    details = "Minecraft + AutoBE"
            
            # Add current song to state if music is playing
            current_song = getattr(self, "_current_track_name", None)
            if current_song:
                state = f"{state} • 🎵 {current_song}"
            
            state_str = f"{state} • © CodeNex 2025"
            try:
                self.discord_rpc.update(
                    details=details,
                    state=state_str,
                    large_image="autobediscord",
                    large_text="AutoBE by CodeNex",
                    start=int(_datetime.datetime.now().timestamp())
                )
            except Exception:
                try:
                    self.discord_rpc.update(details=details, state=state_str)
                except Exception as e2:
                    raise e2
        except Exception as e:
            _logging.debug("Discord RPC update failed: %s", e)
            self.discord_rpc = None
            _logging.info("Discord RPC disconnected; continuing without presence.")
    
    def _update_discord_merge_progress(self, pack_name, current, total, merge_start_ts):
        """Update Discord RPC to show live merge progress. Rate-limited to once per 15 s."""
        if not self.discord_rpc or not hasattr(self.discord_rpc, "update"):
            return
        now = _time.monotonic()
        last = getattr(self, "_discord_merge_last_update", 0)
        if now - last < 15:
            return
        self._discord_merge_last_update = now
        short = pack_name if len(pack_name) <= 40 else pack_name[:37] + "..."
        try:
            state_str = f"Pack {current}/{total} \u2014 {short} \u2022 \u00a9 CodeNex 2024"
            try:
                self.discord_rpc.update(
                    details=f"Merging {total} addons...",
                    state=state_str,
                    large_image="autobediscord",
                    large_text="AutoBE - CodeNex",
                    start=merge_start_ts
                )
            except Exception:
                self.discord_rpc.update(
                    details=f"Merging {total} addons...",
                    state=state_str
                )
        except Exception as e:
            _logging.debug("Discord RPC merge update failed: %s", e)

    def _on_tab_changed(self, event=None):
        """Called when user switches tabs - update Discord presence and close settings dropdown."""
        if not self._is_root_alive():
            return
        
        try:
            # Close settings dropdown if open when switching tabs
            if hasattr(self, '_settings_dropdown'):
                try:
                    if self._settings_dropdown.winfo_exists():
                        self._close_settings_dropdown()
                except:
                    pass
            
            selected_tab = self.notebook.index(self.notebook.select())
            # Tab order: AutoBE=0, MCPACKER=1, List Maker=2, Help=3, Settings=4
            tab_names = [_("tabs.autobe"), _("tabs.mcpacker"), _("tabs.list_maker"), _("tabs.help"), _("tabs.settings")]
            if 0 <= selected_tab < len(tab_names) and selected_tab != 4:  # Skip Settings tab
                self._update_discord_presence(tab_name=tab_names[selected_tab])
        except Exception:
            pass
    
    
    def _close_discord_rpc(self):
        """Close Discord Rich Presence connection."""
        try:
            if getattr(self, "_discord_refresh_id", None) and getattr(self, "_root", None) and self._root.winfo_exists():
                self._root.after_cancel(self._discord_refresh_id)
        except Exception:
            pass
        self._discord_refresh_id = None
        if not self.discord_rpc:
            return
        try:
            # Clear the activity first so Discord removes the presence immediately
            if hasattr(self.discord_rpc, "clear"):
                self.discord_rpc.clear()
        except Exception:
            pass
        try:
            if hasattr(self.discord_rpc, "close"):
                self.discord_rpc.close()
        except Exception:
            pass
        self.discord_rpc = None
    
    def _is_root_alive(self):
        """Safely check if root window exists without raising exceptions."""
        try:
            return self._root and self._root.winfo_exists()
        except (_tk.TclError, RuntimeError):
            return False
    
    def _is_pack_obfuscated(self, file_path):
            """Checks if a pack contains closed-source/obfuscated JSON files."""
            try:
                with _zipfile.ZipFile(file_path, 'r') as pack:
                    for name in pack.namelist():
                        if name.endswith('.json'):
                            with pack.open(name) as f:
                                try:
                                    # Read the beginning of the file to check for protection markers
                                    raw = f.read(2048).decode('utf-8', errors='ignore').strip()
                                    # Marker 1: Starts with */ (illegal JSON syntax used for protection)
                                    # Marker 2: High density of Unicode escapes (\u0065 format)
                                    if raw.startswith('*/') or len(_re.findall(r'\\u[0-9a-fA-F]{4}', raw)) > 15:
                                        return True
                                except:
                                    continue
            except:
                pass
            return False

    def _on_window_close(self):
        """Handle window close attempts - prevent closing during loading."""
        if self._is_loading:
            self._show_close_warning()
        else:
            # Close Discord RPC connection
            self._close_discord_rpc()
            self._root.destroy()
    
    def _show_close_warning(self):
        """Show warning overlay in the main window when user tries to close during loading."""
        if not self._is_root_alive():
            return
        
        # Create warning overlay frame (on top of loading overlay)
        if not hasattr(self, '_warning_overlay'):
            self._warning_overlay = _tk.Frame(self._root, bg='#0A0A0A')
            self._warning_overlay.grid(row=0, column=0, sticky="nsew")
            self._warning_overlay.columnconfigure(0, weight=1)
            self._warning_overlay.rowconfigure(0, weight=1)
        else:
            # Clear existing widgets
            for widget in self._warning_overlay.winfo_children():
                widget.destroy()
        
        # Create centered container
        center_frame = _tk.Frame(self._warning_overlay, bg='#0A0A0A')
        center_frame.place(relx=0.5, rely=0.5, anchor='center')
        
        # Warning icon (using emoji for modern look)
        icon_label = _tk.Label(
            center_frame,
            text="⚠️",
            bg='#0A0A0A',
            fg='#FFAA00',
            font=("Helvetica", 48)
        )
        icon_label.pack(pady=(0, 20))
        
        # Title
        title_label = _tk.Label(
            center_frame,
            text=_("activation.in_progress"),
            bg='#0A0A0A',
            fg='#E1E1E1',
            font=("Helvetica", 18, "bold")
        )
        title_label.pack(pady=(0, 15))
        
        # Message
        message_label = _tk.Label(
            center_frame,
            text=_("activation.please_wait"),
            bg='#0A0A0A',
            fg='#CCCCCC',
            font=("Helvetica", 11),
            justify=_tk.CENTER
        )
        message_label.pack(pady=(0, 25))
        
        # Button container
        button_frame = _tk.Frame(center_frame, bg='#0A0A0A')
        button_frame.pack()
        
        # Continue button (hides warning, returns to loading)
        continue_button = _tk.Button(
            button_frame,
            text=_("activation.continue_waiting"),
            command=self._hide_close_warning,
            bg='#A50CAC',
            fg='#FFFFFF',
            font=("Helvetica", 11, "bold"),
            relief=_tk.FLAT,
            bd=0,
            cursor="hand2",
            activebackground='#8B0A9C',
            activeforeground='#FFFFFF',
            padx=30,
            pady=10,
            width=15
        )
        continue_button.pack()
        
        # Show the warning overlay (on top)
        self._warning_overlay.tkraise()
        
        # Bind Enter and Escape keys
        self._root.bind('<Return>', lambda e: self._hide_close_warning())
        self._root.bind('<Escape>', lambda e: self._hide_close_warning())
    
    def _hide_close_warning(self):
        """Hide warning overlay and return to loading screen."""
        if hasattr(self, '_warning_overlay'):
            self._warning_overlay.grid_remove()
        # Return to loading overlay (which should still be visible underneath)
        if hasattr(self, '_activation_overlay'):
            self._activation_overlay.tkraise()
        # Unbind keys
        self._root.unbind('<Return>')
        self._root.unbind('<Escape>')

    def _get_app_directory(self):
        """Get the directory where the executable/script is located."""
        if getattr(sys, 'frozen', False):
            # Running as compiled executable (PyInstaller)
            app_dir = _os.path.dirname(sys.executable)
        else:
            # Running as script
            app_dir = _os.path.dirname(_os.path.abspath(__file__))
        return app_dir
    
    def _get_settings_path(self):
        """Get the path to the settings file."""
        app_dir = self._get_app_directory()
        cache_dir = _os.path.join(app_dir, ".autobe")
        try:
            _os.makedirs(cache_dir, exist_ok=True)
        except Exception as e:
            log_error(f"Failed to create settings directory: {e}")
        return _os.path.join(cache_dir, "settings.be")

    # Internal storage: obscure names and encoded content so users don't see "hwid"/"blacklist" or raw data.
    _AB_VERIFIED_FILE = ".ab"
    _AB_CACHE_FILE = ".ac"
    _AB_FINGERPRINT_FILE = ".af"

    def _get_verified_hwids_path(self):
        """Internal path for verified device state (not user-visible)."""
        cache_dir = _os.path.dirname(self._get_settings_path())
        return _os.path.join(cache_dir, self._AB_VERIFIED_FILE)

    def _get_blacklist_cache_path(self):
        """Internal path for block cache (not user-visible)."""
        cache_dir = _os.path.dirname(self._get_settings_path())
        return _os.path.join(cache_dir, self._AB_CACHE_FILE)

    def _get_fingerprint_store_path(self):
        """Internal path for device fingerprint binding (HWID -> fingerprint hash)."""
        cache_dir = _os.path.dirname(self._get_settings_path())
        return _os.path.join(cache_dir, self._AB_FINGERPRINT_FILE)

    def _clear_local_cache_files(self):
        """Clear all local cache files to fix false bans on reinstall.
        Only clears if version changed (indicates update/reinstall), not every launch."""
        cache_dir = _os.path.dirname(self._get_settings_path())
        version_file = _os.path.join(cache_dir, ".av")  # AutoBE Version file

        # Check if this is a new version (reinstall/update)
        current_version = APP_VERSION
        stored_version = None
        try:
            if _os.path.isfile(version_file):
                with open(version_file, "r", encoding="utf-8") as f:
                    stored_version = f.read().strip()
        except Exception:
            pass

        # Only clear cache if version changed (reinstall/update) or no version file (first install)
        if stored_version is None or stored_version != current_version:
            cache_files = [
                self._AB_VERIFIED_FILE,
                self._AB_CACHE_FILE,
                self._AB_FINGERPRINT_FILE
            ]
            cleared = []
            for filename in cache_files:
                path = _os.path.join(cache_dir, filename)
                if _os.path.isfile(path):
                    try:
                        _os.remove(path)
                        cleared.append(filename)
                    except Exception as e:
                        _logging.debug(f"Failed to clear cache file {filename}: {e}")
            if cleared:
                _logging.info(f"Cleared local cache files on version change ({stored_version} -> {current_version}): {cleared}")

            # Update stored version
            try:
                _os.makedirs(cache_dir, exist_ok=True)
                with open(version_file, "w", encoding="utf-8") as f:
                    f.write(current_version)
            except Exception:
                pass

    @staticmethod
    def _block_hash(hwid):
        """One-way hash so we never store actual IDs locally (verified or blocked). Cannot be reversed to get ID."""
        return hashlib.sha256((hwid or "").strip().encode("utf-8")).hexdigest()

    def _set_file_hidden_if_windows(self, path):
        """Set file hidden on Windows so it doesn't show in normal folder view."""
        try:
            if platform.system() == "Windows" and _os.path.isfile(path):
                _ctypes.windll.kernel32.SetFileAttributesW(path, 0x02)  # FILE_ATTRIBUTE_HIDDEN
        except Exception:
            pass

    def _load_verified_hwids(self):
        """Load set of hashes only — no actual IDs stored. For offline check we match current device by hash."""
        path = self._get_verified_hwids_path()
        out = set()
        try:
            if _os.path.isfile(path):
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        # New format: 64-char hex (SHA256) — no ID, cannot be reversed
                        if len(line) == 64 and all(c in "0123456789abcdef" for c in line.lower()):
                            out.add(line.lower())
                        else:
                            # Old format: base64 ID — hash it and keep only hash
                            try:
                                decoded = base64.b64decode(line).decode("utf-8", errors="ignore").strip()
                                if decoded:
                                    out.add(self._block_hash(decoded))
                            except Exception:
                                pass
            # Migrate from old plain-text file if present (one-time)
            old_path = _os.path.join(_os.path.dirname(path), "verified_hwids.txt")
            if _os.path.isfile(old_path) and not out:
                with open(old_path, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        h = line.strip()
                        if h:
                            out.add(self._block_hash(h))
                try:
                    _os.makedirs(_os.path.dirname(path), exist_ok=True)
                    with open(path, "w", encoding="utf-8") as g:
                        for h in out:
                            g.write(h + "\n")
                    self._set_file_hidden_if_windows(path)
                    _os.remove(old_path)
                except Exception:
                    pass
        except Exception:
            pass
        return out

    def _save_verified_hwid(self, hwid):
        """Save this device as verified (only when activated online). Only a one-way hash is stored — no ID visible."""
        if not hwid or not hwid.strip():
            return
        hwid = hwid.strip()
        path = self._get_verified_hwids_path()
        try:
            h = self._block_hash(hwid)
            existing = self._load_verified_hwids()
            if h in existing:
                return
            _os.makedirs(_os.path.dirname(path), exist_ok=True)
            with open(path, "a", encoding="utf-8") as f:
                f.write(h + "\n")
            self._set_file_hidden_if_windows(path)
        except Exception as e:
            _logging.debug("Save verified state failed: %s", e)

    def _remove_verified_hwid(self, hwid):
        """Remove this device from local verified (e.g. when online and no longer on GitHub whitelist). Keeps offline in sync with GitHub."""
        if not hwid or not hwid.strip():
            return
        path = self._get_verified_hwids_path()
        try:
            existing = self._load_verified_hwids()
            existing.discard(self._block_hash(hwid.strip()))
            _os.makedirs(_os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                for h in existing:
                    f.write(h + "\n")
            self._set_file_hidden_if_windows(path)
        except Exception as e:
            _logging.debug("Remove verified state failed: %s", e)

    def _get_device_fingerprint(self):
        """Stable hardware fingerprint (hash) for this machine. Used to detect HWID spoofing: same HWID on different hardware = different fingerprint."""
        parts = []
        try:
            if platform.system() == "Windows":
                try:
                    out = subprocess.check_output(
                        ["wmic", "baseboard", "get", "serialnumber"],
                        stderr=subprocess.STDOUT, text=True, timeout=5
                    )
                    serial = next((l.strip().lower() for l in out.splitlines() if l.strip() and "serialnumber" not in l.lower()), "")
                    parts.append(serial or "?")
                except Exception:
                    parts.append("?")
                try:
                    out = subprocess.check_output(
                        ["wmic", "cpu", "get", "processorid"],
                        stderr=subprocess.STDOUT, text=True, timeout=5
                    )
                    pid = next((l.strip().lower() for l in out.splitlines() if l.strip() and "processorid" not in l.lower()), "")
                    parts.append(pid or "?")
                except Exception:
                    parts.append("?")
                try:
                    out = subprocess.check_output(
                        ["wmic", "diskdrive", "get", "serialnumber"],
                        stderr=subprocess.STDOUT, text=True, timeout=5
                    )
                    serials = [l.strip().lower() for l in out.splitlines() if l.strip() and "serialnumber" not in l.lower()]
                    parts.append("|".join(serials) if serials else "?")
                except Exception:
                    parts.append("?")
                try:
                    out = subprocess.check_output(
                        ["wmic", "bios", "get", "version"],
                        stderr=subprocess.STDOUT, text=True, timeout=5
                    )
                    ver = next((l.strip().lower() for l in out.splitlines() if l.strip() and "version" not in l.lower()), "")
                    parts.append(ver or "?")
                except Exception:
                    parts.append("?")
            elif platform.system() == "Linux":
                try:
                    with open("/etc/machine-id", "r", encoding="utf-8", errors="ignore") as f:
                        parts.append(f.read().strip() or "?")
                except Exception:
                    parts.append(platform.node() or "?")
                for name in ["product_uuid", "product_serial", "board_serial"]:
                    try:
                        path = _os.path.join("/sys/class/dmi/id", name)
                        if _os.path.isfile(path):
                            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                                parts.append(f.read().strip() or "?")
                            break
                    except Exception:
                        pass
                if len(parts) < 2:
                    parts.append(platform.node() or "?")
            elif platform.system() == "Darwin":
                try:
                    out = subprocess.check_output(
                        ["system_profiler", "SPHardwareDataType"],
                        stderr=subprocess.DEVNULL, text=True, timeout=10
                    )
                    for line in out.splitlines():
                        if "Serial Number" in line or "Hardware UUID" in line:
                            parts.append(line.strip().lower())
                    if not parts:
                        parts.append(platform.node() or "?")
                except Exception:
                    parts.append(platform.node() or "?")
            else:
                parts.append(platform.node() or "?")
        except Exception:
            parts.append(platform.node() or "?")
        raw = "|".join(parts) if parts else platform.node() or "fp"
        return hashlib.sha256(raw.encode("utf-8", errors="replace")).hexdigest()

    def _load_fingerprint_store(self):
        """Load HWID hash -> fingerprint hash map (one binding per HWID, first activation wins)."""
        path = self._get_fingerprint_store_path()
        out = {}
        try:
            if _os.path.isfile(path):
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        line = line.strip()
                        if not line or "\t" not in line and " " not in line:
                            continue
                        sep = "\t" if "\t" in line else " "
                        a, b = line.split(sep, 1)
                        a, b = a.strip().lower(), b.strip().lower()
                        if len(a) == 64 and len(b) == 64 and all(c in "0123456789abcdef" for c in a + b):
                            out[a] = b
        except Exception:
            pass
        return out

    def _save_fingerprint_for_hwid(self, hwid_hash, fingerprint_hash):
        """Store fingerprint for this HWID only if not already set (first device to activate with this HWID is the bound device)."""
        if not hwid_hash or not fingerprint_hash or len(hwid_hash) != 64 or len(fingerprint_hash) != 64:
            return
        path = self._get_fingerprint_store_path()
        try:
            store = self._load_fingerprint_store()
            if hwid_hash in store:
                return
            store[hwid_hash] = fingerprint_hash
            _os.makedirs(_os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                for h, fp in store.items():
                    f.write(h + " " + fp + "\n")
            self._set_file_hidden_if_windows(path)
        except Exception as e:
            _logging.debug("Save fingerprint binding failed: %s", e)

    def _get_stored_fingerprint(self, hwid_hash):
        """Return stored fingerprint hash for this HWID, or None if never bound."""
        store = self._load_fingerprint_store()
        return store.get(hwid_hash)

    def _deny_and_blacklist_spoofed_hwid(self, _hwid, reason="Device binding mismatch (HWID may be spoofed)."):
        """Remove from verified, add to blacklist (GitHub + cache), show denied. All automatic."""
        self._remove_verified_hwid(_hwid)
        try:
            self._append_to_blacklist(_hwid)
        except Exception as e:
            log_error(f"Failed to add spoofed HWID to blacklist: {e}")
        self._append_to_blacklist_cache(_hwid)
        denied_message = f"{reason}\nAccess denied."
        if self._is_root_alive():
            try:
                self._root.deiconify()
                self._root.update_idletasks()
            except Exception:
                pass
            self._root.after(100, lambda: self._show_denied_screen(denied_message))
        else:
            _messagebox.showerror(_("msg.spoofer_detected"), denied_message)
            sys.exit()
