class AutoBEApp:

    def _load_cached_blacklist(self):
        """Load cached block list as set of hashes only. No actual IDs stored — users can't get blocked IDs."""
        path = self._get_blacklist_cache_path()
        out = set()
        try:
            had_old_format = False
            if _os.path.isfile(path):
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        # New format: 64-char hex (SHA256 hash) — no ID, cannot be reversed
                        if len(line) == 64 and all(c in "0123456789abcdef" for c in line.lower()):
                            out.add(line.lower())
                        else:
                            # Old format: base64-encoded ID — hash it and keep only the hash
                            had_old_format = True
                            try:
                                decoded = base64.b64decode(line).decode("utf-8", errors="ignore").strip()
                                if decoded:
                                    out.add(self._block_hash(decoded))
                            except Exception:
                                pass
            # Migrate from old plain-text file if present (one-time)
            old_path = _os.path.join(_os.path.dirname(path), "blacklist_cache.txt")
            if _os.path.isfile(old_path) and not out:
                with open(old_path, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        h = line.strip()
                        if h:
                            out.add(self._block_hash(h))
                had_old_format = True
                try:
                    _os.makedirs(_os.path.dirname(path), exist_ok=True)
                    with open(path, "w", encoding="utf-8") as g:
                        for h in out:
                            g.write(h + "\n")
                    self._set_file_hidden_if_windows(path)
                    _os.remove(old_path)
                except Exception:
                    pass
            # If file had old format (IDs), re-save as hashes only so no ID is ever stored
            if had_old_format and out:
                try:
                    _os.makedirs(_os.path.dirname(path), exist_ok=True)
                    with open(path, "w", encoding="utf-8") as g:
                        for h in out:
                            g.write(h + "\n")
                    self._set_file_hidden_if_windows(path)
                except Exception:
                    pass
        except Exception:
            pass
        return out

    def _save_blacklist_cache(self, blacklist_text):
        """Save block list as hashes only when we fetch from GitHub. No actual IDs written — users never see blocked IDs."""
        if not blacklist_text or not blacklist_text.strip():
            return
        path = self._get_blacklist_cache_path()
        try:
            _os.makedirs(_os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                for line in blacklist_text.strip().splitlines():
                    line = line.strip()
                    if line:
                        f.write(self._block_hash(line) + "\n")
            self._set_file_hidden_if_windows(path)
        except Exception as e:
            _logging.debug("Save cache failed: %s", e)

    def _append_to_blacklist_cache(self, hwid):
        """Add a blocked device by hash only. The actual ID is never stored — users can't get it."""
        if not hwid or not hwid.strip():
            return
        h = self._block_hash(hwid)
        path = self._get_blacklist_cache_path()
        try:
            existing = self._load_cached_blacklist()
            if h in existing:
                return
            _os.makedirs(_os.path.dirname(path), exist_ok=True)
            with open(path, "a", encoding="utf-8") as f:
                f.write(h + "\n")
            self._set_file_hidden_if_windows(path)
        except Exception as e:
            _logging.debug("Append to cache failed: %s", e)

    def _ensure_music_credits_file(self):
        """Copy MUSIC_CREDITS.txt into the user's .autobe folder so they have the credit link (YouTube) after install."""
        try:
            settings_path = self._get_settings_path()
            cache_dir = _os.path.dirname(settings_path)
            source = _os.path.join(getattr(sys, '_MEIPASS', _BASE_DIR), 'MUSIC_CREDITS.txt')
            if not _os.path.isfile(source):
                source = _os.path.join(_BASE_DIR, 'MUSIC_CREDITS.txt')
            if not _os.path.isfile(source):
                return
            dest = _os.path.join(cache_dir, 'MUSIC_CREDITS.txt')
            if _os.path.isfile(dest):
                return
            _shutil.copy2(source, dest)
        except Exception:
            pass
    
    def _load_settings(self):
        """Load settings from file."""
        settings_path = self._get_settings_path()
        default_settings = {
            "mcpacker_mode": "pack",
            "lang": "en",
            "merge_by_version": False,
            "customize_pack_after_merge": False,
            "show_linked_packs_after_merge": False,
            "background_music": True,
            "background_music_volume": 70,
            "music_shuffle": True,
            "music_playlist": "__all__",
            "auto_import": False,
            "mc_path": "",
            "extendedbe_enabled": False
        }
        try:
            if _os.path.exists(settings_path):
                with open(settings_path, 'r', encoding='utf-8') as f:
                    loaded = _json.load(f)
                    # Merge with defaults to ensure all settings exist
                    default_settings.update(loaded)
            return default_settings
        except Exception as e:
            log_error(f"Failed to load settings: {e}")
            return default_settings
    
    def _save_settings(self, *args):
        """Save current settings to file."""
        # Prevent saving during initialization
        if not hasattr(self, 'mcpacker_mode_var') or not hasattr(self, 'merge_by_version_var'):
            return
        
        settings_path = self._get_settings_path()
        try:
            settings = {
                "mcpacker_mode": self.mcpacker_mode_var.get(),
                "lang": getattr(self, "_current_lang", "en"),
                "merge_by_version": getattr(self, "merge_by_version_var", _tk.BooleanVar(value=False)).get(),
                "customize_pack_after_merge": getattr(self, "customize_pack_after_merge_var", _tk.BooleanVar(value=False)).get(),
                "show_linked_packs_after_merge": getattr(self, "show_linked_packs_after_merge_var", _tk.BooleanVar(value=False)).get(),
                "background_music": getattr(self, "background_music_var", _tk.BooleanVar(value=True)).get(),
                "background_music_volume": getattr(self, "background_music_volume_var", _tk.IntVar(value=70)).get(),
                "music_shuffle": getattr(self, "music_shuffle_var", _tk.BooleanVar(value=True)).get(),
                "music_playlist": getattr(self, "music_playlist_var", _tk.StringVar(value="__all__")).get(),
                "auto_import": getattr(self, "_auto_import_var", _tk.BooleanVar(value=False)).get(),
                "mc_path": getattr(self, "_mc_path_var", _tk.StringVar(value="")).get(),
                "extendedbe_enabled": getattr(self, "extendedbe_enabled_var", _tk.BooleanVar(value=False)).get()
            }
            # Ensure directory exists
            cache_dir = _os.path.dirname(settings_path)
            _os.makedirs(cache_dir, exist_ok=True)
            
            with open(settings_path, 'w', encoding='utf-8') as f:
                _json.dump(settings, f, indent=2)
            _logging.debug(f"Settings saved to: {settings_path}")
        except Exception as e:
            log_error(f"Failed to save settings: {e}")
            _logging.debug(f"Settings path was: {settings_path}")
            import traceback
            _logging.debug(traceback.format_exc())

    def _sanitize_playlist_key(self, value):
        """Normalize playlist key and block path traversal values."""
        try:
            s = str(value or "__all__").strip()
            if not s:
                return "__all__"
            s = s.replace("\\", "/").strip("/")
            if not s or s == "__all__":
                return "__all__"
            parts = [p for p in s.split("/") if p and p != "."]
            if not parts or any(p == ".." for p in parts):
                return "__all__"
            return "/".join(parts)
        except Exception:
            return "__all__"

    def _iter_supported_audio_files(self, base_dir):
        """Yield supported audio files recursively from base_dir."""
        supported = ('.ogg', '.mp3', '.wav')
        for root, _dirs, files in _os.walk(base_dir):
            for name in files:
                if not name or name.startswith('.'):
                    continue
                if _os.path.splitext(name)[1].lower() in supported:
                    path = _os.path.join(root, name)
                    if _os.path.isfile(path):
                        yield path

    def _get_available_music_playlists(self):
        """Return sorted playlist keys from subfolders under music roots."""
        playlists = set()
        for music_dir in _MUSIC_DIRS:
            if not music_dir or not _os.path.isdir(music_dir):
                continue
            try:
                for name in _os.listdir(music_dir):
                    if not name or name.startswith('.'):
                        continue
                    folder = _os.path.join(music_dir, name)
                    if _os.path.isdir(folder):
                        playlists.add(name.replace("\\", "/").strip("/"))
            except OSError:
                continue
        return sorted(playlists, key=lambda x: x.lower())

    def _get_music_file_list(self):
        """Return supported music files from selected playlist or all music."""
        paths = []
        selected_playlist = self._sanitize_playlist_key(
            getattr(self, "music_playlist_var", _tk.StringVar(value="__all__")).get()
        )
        for music_dir in _MUSIC_DIRS:
            if not music_dir or not _os.path.isdir(music_dir):
                continue
            try:
                if selected_playlist == "__all__":
                    for path in self._iter_supported_audio_files(music_dir):
                        if path not in paths:
                            paths.append(path)
                else:
                    playlist_dir = _os.path.join(music_dir, selected_playlist)
                    if _os.path.isdir(playlist_dir):
                        for path in self._iter_supported_audio_files(playlist_dir):
                            if path not in paths:
                                paths.append(path)
            except OSError as e:
                _logging.debug("Background music: could not list %s: %s", music_dir, e)
        if not paths:
            _logging.error(
                "Background music: no playable files for playlist '%s' (checked: %s)",
                selected_playlist,
                _MUSIC_DIRS,
            )
        return paths

    def _rebuild_music_order(self, keep_current=True):
        """Build playback order based on current files and shuffle setting."""
        paths = self._get_music_file_list()
        if not paths:
            self._music_order = []
            self._music_index = -1
            return []
        order = list(paths)
        if getattr(self, "music_shuffle_var", None) and self.music_shuffle_var.get():
            _random.shuffle(order)
        else:
            order.sort(key=lambda p: self._format_track_display_name(p).lower())
        # Prefer a canonical "background.*" track as first song when starting fresh.
        if order and int(getattr(self, "_music_index", -1)) < 0:
            preferred_idx = -1
            for i, p in enumerate(order):
                n = _os.path.splitext(_os.path.basename(p))[0].strip().lower()
                if n == "background":
                    preferred_idx = i
                    break
            if preferred_idx < 0:
                for i, p in enumerate(order):
                    n = _os.path.splitext(_os.path.basename(p))[0].strip().lower()
                    if n.startswith("background"):
                        preferred_idx = i
                        break
            if preferred_idx > 0:
                preferred = order.pop(preferred_idx)
                order.insert(0, preferred)
        current_path = getattr(self, "_current_track_path", None) if keep_current else None
        self._music_order = order
        if current_path and current_path in order:
            self._music_index = order.index(current_path)
        else:
            self._music_index = -1
        return order

    def _play_track_at_index(self, index, show_popup=True, popup_force=False):
        """Play the track at index in current music order. Returns True on success."""
        if not _PYGAME_MIXER_AVAILABLE or _pygame is None:
            return False
        order = list(getattr(self, "_music_order", []) or [])
        if not order:
            return False
        total = len(order)
        start = index % total
        last_err = None
        for offset in range(total):
            idx = (start + offset) % total
            path = order[idx]
            try:
                _pygame.mixer.music.load(path)
                _pygame.mixer.music.set_volume(self._get_music_volume())
                _pygame.mixer.music.play(loops=0)
                self._music_index = idx
                self._current_track_path = path
                self._current_track_name = self._format_track_display_name(path)
                # Re-apply volume shortly after play for pygame/Windows edge cases.
                def _reapply_vol():
                    try:
                        if _pygame and _pygame.mixer.get_init():
                            _pygame.mixer.music.set_volume(self._get_music_volume())
                    except Exception:
                        pass
                self._root.after(200, _reapply_vol)
                self._root.after(600, _reapply_vol)
                if show_popup:
                    self._show_now_playing(self._current_track_name, force=popup_force)
                # Update Discord presence with new song
                self._update_discord_presence()
                return True
            except Exception as e:
                last_err = e
                continue
        _logging.error("Background music: failed to play any track in current order. Last error: %s", last_err)
        return False

    def _play_next_track(self, show_popup=True, popup_force=False):
        """Play next track based on current order and shuffle setting."""
        try:
            if not getattr(self, "background_music_var", None) or not self.background_music_var.get():
                return False
            if not _PYGAME_MIXER_AVAILABLE or _pygame is None:
                return False
            current_path = getattr(self, "_current_track_path", None)
            current_files = self._get_music_file_list()
            if not current_files:
                return False
            order = list(getattr(self, "_music_order", []) or [])
            if (not order) or (set(order) != set(current_files)):
                order = self._rebuild_music_order(keep_current=True)
            if not order:
                return False
            idx = int(getattr(self, "_music_index", -1))
            if idx < 0 and current_path in order:
                idx = order.index(current_path)
                self._music_index = idx
            next_idx = idx + 1
            if next_idx >= len(order):
                if getattr(self, "music_shuffle_var", None) and self.music_shuffle_var.get():
                    last_path = current_path
                    _random.shuffle(order)
                    if last_path and len(order) > 1 and order[0] == last_path:
                        order.append(order.pop(0))
                    self._music_order = order
                next_idx = 0
            return self._play_track_at_index(next_idx, show_popup=show_popup, popup_force=popup_force)
        except Exception as e:
            _logging.error("Background music _play_next_track: %s", e)
            return False

    def _play_previous_track(self, show_popup=True, popup_force=False):
        """Play previous track based on current order."""
        try:
            if not getattr(self, "background_music_var", None) or not self.background_music_var.get():
                return False
            if not _PYGAME_MIXER_AVAILABLE or _pygame is None:
                return False
            order = list(getattr(self, "_music_order", []) or [])
            if not order:
                order = self._rebuild_music_order(keep_current=True)
            if not order:
                return False
            idx = int(getattr(self, "_music_index", -1))
            current_path = getattr(self, "_current_track_path", None)
            if idx < 0 and current_path in order:
                idx = order.index(current_path)
                self._music_index = idx
            prev_idx = (idx - 1) if idx > 0 else (len(order) - 1)
            return self._play_track_at_index(prev_idx, show_popup=show_popup, popup_force=popup_force)
        except Exception as e:
            _logging.error("Background music _play_previous_track: %s", e)
            return False

    def _start_music_end_watcher(self):
        """Ensure a single watcher advances track after current one ends."""
        if getattr(self, "_music_end_after_id", None) is not None:
            return
        def _poll():
            self._music_end_after_id = None
            try:
                if not getattr(self, "_root", None) or not self._root.winfo_exists():
                    return
                if not getattr(self, "background_music_var", None) or not self.background_music_var.get():
                    return
                busy = False
                try:
                    busy = bool(_PYGAME_MIXER_AVAILABLE and _pygame and _pygame.mixer.get_init() and _pygame.mixer.music.get_busy())
                except Exception:
                    busy = False
                if not busy:
                    self._play_next_track(show_popup=True, popup_force=True)
            except Exception:
                pass
            finally:
                if getattr(self, "_root", None) and self._root.winfo_exists() and getattr(self, "background_music_var", None) and self.background_music_var.get():
                    self._music_end_after_id = self._root.after(1200, _poll)
        self._music_end_after_id = self._root.after(1200, _poll)

    def _stop_music_end_watcher(self):
        """Stop track-end watcher timer."""
        if getattr(self, "_music_end_after_id", None) is not None:
            try:
                self._root.after_cancel(self._music_end_after_id)
            except Exception:
                pass
            self._music_end_after_id = None

    def _on_music_shuffle_setting_changed(self):
        """Rebuild order while keeping current track when shuffle mode changes."""
        try:
            self._rebuild_music_order(keep_current=True)
        except Exception:
            pass

    def _on_music_playlist_setting_changed(self):
        """Apply selected playlist and restart from that list when needed."""
        try:
            selected = self._sanitize_playlist_key(
                getattr(self, "music_playlist_var", _tk.StringVar(value="__all__")).get()
            )
            if getattr(self, "music_playlist_var", None) and self.music_playlist_var.get() != selected:
                self.music_playlist_var.set(selected)
                return
            self._rebuild_music_order(keep_current=False)
            if getattr(self, "_root", None) and self._root.winfo_exists():
                refresh_fn = getattr(self, "_settings_refresh_now_playing", None)
                if callable(refresh_fn):
                    try:
                        self._root.after(0, refresh_fn)
                    except Exception:
                        pass
            if not getattr(self, "background_music_var", None) or not self.background_music_var.get():
                return
            if not _PYGAME_MIXER_AVAILABLE or _pygame is None:
                return
            if not getattr(self, "_music_order", None):
                try:
                    _pygame.mixer.music.stop()
                except Exception:
                    pass
                self._current_track_name = None
                self._current_track_path = None
                # Update Discord presence to clear song
                self._update_discord_presence()
                return
            self._play_track_at_index(0, show_popup=True, popup_force=True)
            self._start_music_end_watcher()
        except Exception:
            pass

    def _format_track_display_name(self, value):
        """Create a clean human-readable track title from filename/path."""
        try:
            if value is None:
                return "Unknown"
            raw = str(value).strip()
            if not raw:
                return "Unknown"
            # Accept either full path or filename/title
            name = _os.path.splitext(_os.path.basename(raw))[0]
            # Remove common numeric prefixes like "01 - " / "001_" / "12. "
            name = _re.sub(r'^\s*\d+\s*[-_.\)\]]+\s*', '', name)
            # Normalize separators and whitespace
            name = name.replace('_', ' ').strip()
            name = _re.sub(r'\s{2,}', ' ', name)
            return name or "Unknown"
        except Exception:
            return "Unknown"

    def _ellipsize_text(self, text, tk_font, max_width):
        """Trim text with ellipsis so it fits within max_width pixels."""
        try:
            s = str(text or "")
            if not s:
                return ""
            if tk_font.measure(s) <= max_width:
                return s
            ell = "..."
            if tk_font.measure(ell) > max_width:
                return ""
            lo, hi = 0, len(s)
            while lo < hi:
                mid = (lo + hi + 1) // 2
                cand = s[:mid].rstrip() + ell
                if tk_font.measure(cand) <= max_width:
                    lo = mid
                else:
                    hi = mid - 1
            return s[:lo].rstrip() + ell
        except Exception:
            return str(text or "")

    def _play_next_shuffled_track(self):
        """Play one random track from the music folder; when it ends, schedule the next (shuffle)."""
        self._play_next_track(show_popup=True, popup_force=True)

    def _start_background_music(self):
        """Play non-copyright background music from music/ folder (shuffled). Turn on/off in Settings."""
        try:
            if not getattr(self, "background_music_var", None) or not self.background_music_var.get():
                return
            if not _PYGAME_MIXER_AVAILABLE or _pygame is None:
                return
            # Initialize full pygame first (helps mixer on some Windows setups)
            try:
                _pygame.init()
            except Exception:
                pass
            if not _pygame.mixer.get_init():
                for kwargs in [
                    {"frequency": 44100, "size": -16, "channels": 2, "buffer": 512},
                    {"frequency": 22050, "size": -16, "channels": 2, "buffer": 1024},
                    {},
                ]:
                    try:
                        if kwargs:
                            _pygame.mixer.init(**kwargs)
                        else:
                            _pygame.mixer.init()
                        break
                    except Exception as e:
                        _logging.error("pygame.mixer.init failed: %s", e)
                        if not kwargs:
                            return
            # If music is already playing, don't restart/reorder; just keep watcher alive.
            try:
                if _pygame.mixer.get_init() and _pygame.mixer.music.get_busy() and getattr(self, "_current_track_path", None):
                    self._start_music_end_watcher()
                    return
            except Exception:
                pass
            try:
                _pygame.mixer.music.stop()
            except Exception:
                pass
            self._rebuild_music_order(keep_current=False)
            self._play_next_track(show_popup=True, popup_force=True)
            self._start_music_end_watcher()
        except Exception as e:
            _logging.error("_start_background_music: %s", e)

    def _show_now_playing(self, track_name, force=False):
        """Show an in-app 'Now Playing' popup with fade in/out animation."""
        try:
            if not getattr(self, "_root", None) or not self._root.winfo_exists():
                return
            track_name = self._format_track_display_name(track_name)
            _now = _time.monotonic()
            _last_popup_at = float(getattr(self, "_last_now_playing_at", 0.0) or 0.0)
            _last_popup_track = getattr(self, "_last_now_playing_track", None)
            # Always show popup on genuine song changes. Only suppress rapid duplicate spam.
            if not force and _last_popup_track == track_name and (_now - _last_popup_at) < 0.7:
                return
            self._last_now_playing_at = _now
            self._last_now_playing_track = track_name
            self._now_playing_anim_token = int(getattr(self, "_now_playing_anim_token", 0)) + 1
            _token = self._now_playing_anim_token
            # Cancel any existing now-playing popup
            if getattr(self, "_now_playing_popup", None) and self._now_playing_popup.winfo_exists():
                try:
                    self._now_playing_popup.destroy()
                except Exception:
                    pass
            if getattr(self, "_now_playing_after_id", None) is not None:
                try:
                    self._root.after_cancel(self._now_playing_after_id)
                except Exception:
                    pass
                self._now_playing_after_id = None
            if getattr(self, "_now_playing_marquee_after_id", None) is not None:
                try:
                    self._root.after_cancel(self._now_playing_marquee_after_id)
                except Exception:
                    pass
                self._now_playing_marquee_after_id = None
            popup_w, popup_h = 300, 72
            pw = _tk.Frame(self._root, bg="#1a1a1a", highlightthickness=1, highlightbackground="#9333ea", bd=0)
            inner = _tk.Frame(pw, bg="#1a1a1a", padx=16, pady=12)
            inner.pack(fill="both", expand=True)
            header_lbl = _tk.Label(inner, text="Now Playing", bg="#1a1a1a", fg="#9333ea", font=("Segoe UI", 10, "bold"))
            header_lbl.pack(anchor="w")
            _text_font = _font.Font(family="Segoe UI", size=12)
            _text_label_w = popup_w - 32
            track_canvas = _tk.Canvas(inner, width=_text_label_w, height=22, bg="#1a1a1a", highlightthickness=0)
            track_canvas.pack(anchor="w", fill="x")
            _popup_np_text = track_name or "Unknown"
            _popup_np_width = _text_font.measure(_popup_np_text)
            _track_text_item = None
            if _popup_np_width <= _text_label_w:
                _track_text_item = track_canvas.create_text(_text_label_w // 2, 11, text=_popup_np_text, fill="#FFFFFF", font=("Segoe UI", 12), anchor="center")
            else:
                _gap = "     "
                _loop_text = _popup_np_text + _gap + _popup_np_text
                _reset_at = _text_font.measure(_popup_np_text + _gap)
                _tid = track_canvas.create_text(0, 11, text=_loop_text, fill="#FFFFFF", font=("Segoe UI", 12), anchor="w")
                _track_text_item = _tid
                _x = [0.0]
                _SCROLL_MS = 16  # ~60 FPS
                _SCROLL_PX = 0.8
                def _popup_marquee_step():
                    if _token != getattr(self, "_now_playing_anim_token", -1):
                        return
                    if not pw.winfo_exists() or not track_canvas.winfo_exists():
                        return
                    try:
                        track_canvas.coords(_tid, _x[0], 11)
                        _x[0] -= _SCROLL_PX
                        if _x[0] <= -_reset_at:
                            _x[0] = 0.0
                        self._now_playing_marquee_after_id = self._root.after(_SCROLL_MS, _popup_marquee_step)
                    except Exception:
                        pass
                self._now_playing_marquee_after_id = self._root.after(350, _popup_marquee_step)
            self._now_playing_popup = pw
            pw.lift()

            try:
                self._root.update_idletasks()
            except Exception:
                return
            rw = self._root.winfo_width()
            x = max(0, rw // 2 - popup_w // 2)
            y_pos = 16

            def _place():
                if _token != getattr(self, "_now_playing_anim_token", -1):
                    return
                if pw.winfo_exists():
                    pw.place(x=x, y=int(y_pos), width=popup_w, height=popup_h)

            def _hex_to_rgb(value):
                v = str(value or "").lstrip("#")
                if len(v) != 6:
                    return (255, 255, 255)
                return (int(v[0:2], 16), int(v[2:4], 16), int(v[4:6], 16))

            def _rgb_to_hex(rgb):
                r, g, b = [max(0, min(255, int(c))) for c in rgb]
                return f"#{r:02x}{g:02x}{b:02x}"

            def _blend(c0, c1, t):
                t = max(0.0, min(1.0, float(t)))
                a = _hex_to_rgb(c0)
                b = _hex_to_rgb(c1)
                return _rgb_to_hex((
                    a[0] + (b[0] - a[0]) * t,
                    a[1] + (b[1] - a[1]) * t,
                    a[2] + (b[2] - a[2]) * t,
                ))

            def _apply_fade(alpha):
                if _token != getattr(self, "_now_playing_anim_token", -1):
                    return
                if not pw.winfo_exists():
                    return
                # Fake opacity by blending toward root bg.
                try:
                    base_bg = "#1a1a1a"
                    root_bg = "#000000"
                    accent = "#9333ea"
                    text_white = "#ffffff"
                    bg_now = _blend(root_bg, base_bg, alpha)
                    accent_now = _blend(root_bg, accent, alpha)
                    text_now = _blend(root_bg, text_white, alpha)
                    pw.configure(bg=bg_now, highlightbackground=accent_now)
                    inner.configure(bg=bg_now)
                    header_lbl.configure(bg=bg_now, fg=accent_now)
                    track_canvas.configure(bg=bg_now)
                    if _track_text_item is not None:
                        track_canvas.itemconfig(_track_text_item, fill=text_now)
                except Exception:
                    pass

            def _destroy_popup():
                if _token != getattr(self, "_now_playing_anim_token", -1):
                    return
                try:
                    if pw.winfo_exists():
                        pw.place_forget()
                        pw.destroy()
                except Exception:
                    pass
                if getattr(self, "_now_playing_popup", None) is pw:
                    self._now_playing_popup = None
                self._now_playing_after_id = None
                if getattr(self, "_now_playing_marquee_after_id", None) is not None:
                    try:
                        self._root.after_cancel(self._now_playing_marquee_after_id)
                    except Exception:
                        pass
                    self._now_playing_marquee_after_id = None

            def _fade_in(step=0):
                if _token != getattr(self, "_now_playing_anim_token", -1):
                    return
                if not pw.winfo_exists():
                    return
                steps_total = 14
                if step <= steps_total:
                    t = step / steps_total
                    eased = 1 - (1 - t) ** 2
                    _apply_fade(eased)
                    next_step = step + 1
                    self._now_playing_after_id = self._root.after(16, lambda ns=next_step: _fade_in(ns))
                else:
                    self._now_playing_after_id = self._root.after(3000, _fade_out)

            def _fade_out(step=0):
                if _token != getattr(self, "_now_playing_anim_token", -1):
                    return
                if not pw.winfo_exists():
                    return
                steps_total = 16
                if step <= steps_total:
                    t = step / steps_total
                    # Ease-out fade for a soft disappear.
                    alpha = 1 - (t * t)
                    _apply_fade(alpha)
                    next_step = step + 1
                    self._now_playing_after_id = self._root.after(16, lambda ns=next_step: _fade_out(ns))
                else:
                    _destroy_popup()

            _place()
            _apply_fade(0.0)
            self._now_playing_after_id = self._root.after(25, lambda: _fade_in(0))
        except Exception:
            pass

    def _stop_background_music(self):
        """Stop background music."""
        setattr(self, "_current_track_name", None)
        setattr(self, "_current_track_path", None)
        setattr(self, "_music_index", -1)
        self._stop_music_end_watcher()
        # Update Discord presence to clear song
        self._update_discord_presence()
        if not _PYGAME_MIXER_AVAILABLE or _pygame is None:
            return
        try:
            _pygame.mixer.music.stop()
        except Exception:
            pass

    def _get_music_volume(self):
        """Return background music volume as float 0.0–1.0 from settings. If slider is 0, use 0.05 so we don't get silent playback by mistake."""
        v = getattr(self, "background_music_volume_var", None)
        if v is None:
            return 0.7
        raw = min(1.0, max(0.0, v.get() / 100.0))
        return 0.05 if raw == 0 else raw

    def _apply_background_music_volume(self, *args):
        """Apply current music volume to pygame mixer if playing."""
        try:
            if not _PYGAME_MIXER_AVAILABLE or _pygame is None:
                return
            if _pygame.mixer.get_init():
                _pygame.mixer.music.set_volume(self._get_music_volume())
        except Exception:
            pass

    def _apply_background_music_setting(self, *args):
        """Called when background music setting changes: start or stop music."""
        try:
            if getattr(self, "background_music_var", None) and self.background_music_var.get():
                self._start_background_music()
            else:
                self._stop_background_music()
        except Exception:
            pass
    
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

    def _version_tuple(self, v):
        """Convert version string to tuple of ints for comparison."""
        s = str(v).strip().lstrip('vV').splitlines()[0].strip()
        try:
            return tuple(int(x) for x in s.split('.') if x.isdigit())
        except (ValueError, AttributeError):
            return (0,)

    def _get_windows_exe_version(self, exe_path):
        """Read Windows EXE file version (e.g. 7.0.2.0) via PowerShell."""
        if platform.system() != "Windows":
            return None
        try:
            safe = str(exe_path or "").replace("'", "''")
            cmd = f"(Get-Item -LiteralPath '{safe}').VersionInfo.FileVersion"
            flags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
            proc = subprocess.run(
                ["powershell", "-NoProfile", "-Command", cmd],
                capture_output=True,
                text=True,
                timeout=12,
                creationflags=flags,
            )
            out = ((proc.stdout or "") + "\n" + (proc.stderr or "")).strip()
            m = _re.search(r"\d+(?:\.\d+){1,3}", out)
            return m.group(0) if m else None
        except Exception:
            return None

    def _check_for_updates(self):
        """User clicked Check for updates: close dropdown and run check (show 'Up to date' if no update)."""
        self._close_settings_dropdown()
        self._run_update_check(silent_if_up_to_date=False)

    def _run_update_check(self, silent_if_up_to_date=False):
        """Check version.txt line 2 and GitHub Releases. If newer version exists, show Update available. If silent_if_up_to_date, don't show anything when already up to date (used for auto-check on startup)."""
        with self._update_check_lock:
            if getattr(self, '_update_check_in_progress', False):
                return
            self._update_check_in_progress = True

        def do_check():
            try:
                version_text = self._fetch_github_file("version.txt")
                if not version_text:
                    return
                lines = version_text.strip().splitlines()
                latest_str = (lines[1].strip() if len(lines) > 1 else '').lstrip('vV')
                if not latest_str or self._version_tuple(latest_str) <= self._version_tuple(APP_VERSION):
                    if not silent_if_up_to_date:
                        self._root.after(0, lambda: self._show_themed_info_dialog(_("update.title"), _("update.up_to_date") + "\n" + _f("update.current_version", version=APP_VERSION)))
                    return
                headers = {"Accept": "application/vnd.github.v3+json"}
                if GITHUB_TOKEN:
                    headers["Authorization"] = f"token {GITHUB_TOKEN}"
                # Prefer exact tag from version.txt so we never depend on GitHub "latest" ordering.
                tag_candidates = [f"v{latest_str}", latest_str]
                data = None
                last_http = None
                for _tag in tag_candidates:
                    try:
                        url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/tags/{_tag}"
                        r = _requests.get(url, headers=headers, timeout=10)
                        last_http = r.status_code
                        if r.status_code == 200:
                            data = r.json()
                            break
                    except Exception:
                        pass
                if data is None:
                    # Fallback to /latest only if exact-tag lookup failed.
                    try:
                        url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
                        r = _requests.get(url, headers=headers, timeout=10)
                        last_http = r.status_code
                        if r.status_code == 200:
                            data = r.json()
                    except Exception as release_err:
                        log_error(release_err)
                if data is None:
                    if not silent_if_up_to_date:
                        def show_no_release():
                            if hasattr(self, '_settings_dropdown') and self._settings_dropdown.winfo_exists():
                                self._root.after(1000, show_no_release)
                                return
                            self._show_update_available_no_release(latest_str)
                        self._root.after(0, show_no_release)
                    return
                # Ensure release metadata matches version.txt before offering update.
                release_tag = str((data or {}).get("tag_name") or "").strip().lstrip('vV')
                if not release_tag or self._version_tuple(release_tag) != self._version_tuple(latest_str):
                    if not silent_if_up_to_date:
                        def show_no_release():
                            if hasattr(self, '_settings_dropdown') and self._settings_dropdown.winfo_exists():
                                self._root.after(1000, show_no_release)
                                return
                            self._show_update_available_no_release(latest_str)
                        self._root.after(0, show_no_release)
                    return
                if not silent_if_up_to_date:
                    def show():
                        if hasattr(self, '_settings_dropdown') and self._settings_dropdown.winfo_exists():
                            self._root.after(1000, show)
                            return
                        self._show_update_available(latest_str, data)
                    self._root.after(0, show)
            except Exception as e:
                log_error(e)
                if not silent_if_up_to_date:
                    self._root.after(0, lambda: self._show_themed_info_dialog(_("update.title"), _("update.check_failed")))
            finally:
                self._root.after(0, lambda: setattr(self, '_update_check_in_progress', False))

        threading.Thread(target=do_check, daemon=True).start()

    def _auto_check_for_updates(self):
        """Run once after startup: detect new release and show Update available only if one exists. No popup if up to date."""
        self._run_update_check(silent_if_up_to_date=True)

    def _periodic_update_check(self):
        """Background check every UPDATE_CHECK_INTERVAL_MS. Keeps app aware of new releases without opening a dialog when up to date."""
        if getattr(self, '_root', None) and self._root.winfo_exists():
            self._run_update_check(silent_if_up_to_date=True)
            self._root.after(UPDATE_CHECK_INTERVAL_MS, self._periodic_update_check)

    def _show_update_available_no_release(self, new_version):
        """No release found that matches the latest version in version.txt — themed message, OK only. When a release is ready they'll see Update now / Later."""
        if getattr(self, '_update_no_release_dialog_shown', False):
            return
        self._update_no_release_dialog_shown = True
        def on_destroy():
            self._update_no_release_dialog_shown = False
        self._show_themed_info_dialog(_("update.no_release_title"), _f("update.no_release_msg", version=new_version), on_destroy=on_destroy)

    def _show_update_available(self, new_version, release_data):
        """Show themed Update available dialog; on Update now run auto-install."""
        self._show_themed_update_prompt(new_version, release_data)
