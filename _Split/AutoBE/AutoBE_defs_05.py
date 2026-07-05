class AutoBEApp:

    def _show_themed_info_dialog(self, title, message, on_destroy=None, topmost=False):
        """Show themed one-button dialog (e.g. Up to date, or Update not ready). Fixed size, no resize. Optional on_destroy() when dialog is closed."""
        dlg = _tk.Toplevel(self._root)
        self._apply_window_icon(dlg)
        dlg.title(title)
        dlg.configure(bg='#000000')
        w, h = 420, 280
        dlg.geometry(f"{w}x{h}")
        dlg.minsize(w, h)
        dlg.maxsize(w, h)
        dlg.resizable(False, False)
        dlg.overrideredirect(True)
        dlg.transient(self._root)
        dlg.grab_set()
        if topmost:
            try:
                dlg.attributes("-topmost", True)
                dlg.after(1800, lambda: dlg.winfo_exists() and dlg.attributes("-topmost", False))
            except Exception:
                pass
        dlg.update_idletasks()
        rx, ry = self._root.winfo_x(), self._root.winfo_y()
        rw, rh = self._root.winfo_width(), self._root.winfo_height()
        x = rx + max(0, (rw - w) // 2)
        y = ry + max(0, (rh - h) // 2)
        dlg.geometry(f"+{x}+{y}")
        dlg.grid_columnconfigure(0, weight=1)
        dlg.grid_rowconfigure(0, weight=0)
        dlg.grid_rowconfigure(1, weight=1)

        _drag = {"x": 0, "y": 0}
        def _drag_start(event):
            _drag["x"] = event.x_root - dlg.winfo_x()
            _drag["y"] = event.y_root - dlg.winfo_y()
        def _drag_move(event):
            dlg.geometry(f"+{event.x_root - _drag['x']}+{event.y_root - _drag['y']}")

        if on_destroy:
            def _on_destroy(event):
                if event.widget == dlg:
                    try:
                        on_destroy()
                    except Exception:
                        pass
            dlg.bind('<Destroy>', _on_destroy)

        titlebar = _tk.Frame(dlg, bg="#000000", height=34, highlightthickness=1, highlightbackground="#1f1f1f")
        titlebar.grid(row=0, column=0, sticky="ew")
        titlebar.grid_columnconfigure(1, weight=1)
        titlebar.grid_propagate(False)
        dlg._titlebar_icon_img = _get_titlebar_icon_image(14)
        if dlg._titlebar_icon_img is not None:
            title_icon = _tk.Label(titlebar, image=dlg._titlebar_icon_img, bg="#000000")
        else:
            title_icon = _tk.Label(titlebar, text="◈", bg="#000000", fg="#9333ea", font=("Segoe UI", 10, "bold"))
        title_icon.grid(row=0, column=0, padx=(10, 6), sticky="w")
        title_lbl = _tk.Label(titlebar, text=title, bg="#000000", fg="#E5E7EB", font=("Segoe UI", 10, "bold"))
        title_lbl.grid(row=0, column=1, padx=(0, 6), sticky="w")
        _tk.Button(
            titlebar, text="✕", command=dlg.destroy, bg="#000000", fg="#E5E7EB",
            font=("Segoe UI", 10, "bold"), relief="flat", bd=0, padx=12, pady=3,
            activebackground="#c42b1c", activeforeground="#FFFFFF", cursor="hand2"
        ).grid(row=0, column=2, sticky="e")
        for _w in (titlebar, title_icon, title_lbl):
            _w.bind("<ButtonPress-1>", _drag_start, add="+")
            _w.bind("<B1-Motion>", _drag_move, add="+")

        main = _tk.Frame(dlg, bg='#0f1419', padx=24, pady=24)
        main.grid(row=1, column=0, sticky="nsew")
        _tk.Frame(main, bg='#9333ea', height=3).pack(fill='x', pady=(0, 16))
        _tk.Label(main, text=title, bg='#0f1419', fg='#FFFFFF', font=('Segoe UI', 16, 'bold')).pack(anchor='w')
        _tk.Label(main, text=message, bg='#0f1419', fg='#e5e7eb', font=('Segoe UI', 10), justify='left', wraplength=360).pack(anchor='w', pady=(12, 24))
        _tk.Button(main, text=_("common.ok"), command=dlg.destroy, bg='#9333ea', fg='#FFFFFF', font=('Segoe UI', 11, 'bold'), relief='flat', cursor='hand2', activebackground='#a855f7', padx=28, pady=8).pack(anchor='s', pady=(16, 0))

    def _show_themed_update_prompt(self, new_version, release_data):
        """Themed dialog: Update available — Update now / Later. Fixed size, no resize. Click only."""
        dlg = _tk.Toplevel(self._root)
        self._apply_window_icon(dlg)
        dlg.title(_("update.available"))
        dlg.configure(bg='#0f1419')
        w, h = 460, 300
        dlg.geometry(f"{w}x{h}")
        dlg.minsize(w, h)
        dlg.maxsize(w, h)
        dlg.resizable(False, False)
        dlg.transient(self._root)
        dlg.grab_set()
        dlg.update_idletasks()
        rx, ry = self._root.winfo_x(), self._root.winfo_y()
        rw, rh = self._root.winfo_width(), self._root.winfo_height()
        x = rx + max(0, (rw - w) // 2)
        y = ry + max(0, (rh - h) // 2)
        dlg.geometry(f"+{x}+{y}")
        main = _tk.Frame(dlg, bg='#0f1419', padx=24, pady=24)
        main.pack(fill='both', expand=True)
        _tk.Frame(main, bg='#9333ea', height=3).pack(fill='x', pady=(0, 16))
        _tk.Label(main, text=_("update.available"), bg='#0f1419', fg='#FFFFFF', font=('Segoe UI', 16, 'bold')).pack(anchor='w')
        _tk.Label(main, text=_f("update.your_version", current=APP_VERSION, new=new_version), bg='#0f1419', fg='#a78bfa', font=('Segoe UI', 11)).pack(anchor='w', pady=(8, 12))
        _tk.Label(main, text=_("update.will_download"), bg='#0f1419', fg='#e5e7eb', font=('Segoe UI', 10), justify='left').pack(anchor='w', pady=(0, 20))
        btn_frame = _tk.Frame(main, bg='#0f1419')
        btn_frame.pack(fill='x')
        def on_update():
            dlg.destroy()
            self._do_auto_update(release_data, expected_version=new_version)
        def on_later():
            dlg.destroy()
        _tk.Button(btn_frame, text=_("update.now"), command=on_update, bg='#9333ea', fg='#FFFFFF', font=('Segoe UI', 11, 'bold'), relief='flat', cursor='hand2', activebackground='#a855f7', padx=24, pady=10).pack(side='left', padx=(0, 12))
        _tk.Button(btn_frame, text=_("update.later"), command=on_later, bg='#2a2a2a', fg='#e5e7eb', font=('Segoe UI', 11), relief='flat', cursor='hand2', activebackground='#3a3a3a', padx=24, pady=10).pack(side='left')

    def _show_update_overlay_ui(self, status_text):
        """Show full-screen update overlay (themed like verification): title + status + spinner."""
        for w in self._update_overlay.winfo_children():
            w.destroy()
        self._update_overlay.grid_columnconfigure(0, weight=1)
        self._update_overlay.grid_rowconfigure(0, weight=1)
        center = _tk.Frame(self._update_overlay, bg='#000000')
        center.place(relx=0.5, rely=0.5, anchor='center')
        _tk.Label(center, text=_("update.updating"), bg='#000000', fg='#FFFFFF', font=('Segoe UI', 20, 'bold')).pack(pady=(0, 40))
        spinner_frame = _tk.Frame(center, bg='#000000')
        spinner_frame.pack(pady=20)
        dot_colors = ['#FF0000', '#00FF00', '#0000FF', '#FFFF00', '#FF00FF', '#00FFFF']
        self._update_dots = []
        for i in range(6):
            dot = _tk.Label(spinner_frame, text="●", bg='#000000', fg=dot_colors[i], font=('Segoe UI', 24, 'bold'))
            dot.pack(side=_tk.LEFT, padx=5)
            self._update_dots.append(dot)
        self._update_status_label = _tk.Label(center, text=status_text, bg='#000000', fg='#9333ea', font=('Segoe UI', 12))
        self._update_status_label.pack(pady=30)
        self._update_overlay.grid()
        self._update_overlay.lift()
        self._root.update_idletasks()
        self._update_anim_step = 0
        self._update_animate()

    def _update_animate(self):
        """Animate spinner on update overlay."""
        if not hasattr(self, '_update_status_label') or not self._update_status_label.winfo_exists():
            return
        step = getattr(self, '_update_anim_step', 0)
        for i, dot in enumerate(getattr(self, '_update_dots', [])):
            if not dot.winfo_exists():
                return
            phase = (step + i * 60) % 360
            r = int(127.5 * (1 + math.sin(math.radians(phase))))
            g = int(127.5 * (1 + math.sin(math.radians(phase + 120))))
            b = int(127.5 * (1 + math.sin(math.radians(phase + 240))))
            dot.config(fg=f"#{r:02x}{g:02x}{b:02x}")
        self._update_anim_step = step + 5
        self._root.after(50, self._update_animate)

    def _update_overlay_set_status(self, text):
        if hasattr(self, '_update_status_label') and self._update_status_label.winfo_exists():
            self._update_status_label.config(text=text)

    def _do_auto_update(self, release_data, expected_version=None):
        """Run updater (Windows prefers full installer upgrade; fallback to exe swap)."""
        def do_download():
            def fail_update(reason):
                self._root.after(
                    0,
                    lambda msg=reason: self._offer_installer_fallback_update(
                        release_data=release_data,
                        expected_version=expected_version,
                        fail_message=msg,
                    ),
                )
            try:
                self._root.after(0, lambda: self._show_update_overlay_ui(_("update.downloading")))
                assets = release_data.get('assets') or []
                current_exe = sys.executable
                current_name = _os.path.basename(current_exe).lower()
                # Guard: only proceed when release tag matches the version user was prompted for.
                release_tag = str((release_data or {}).get("tag_name") or "").strip().lstrip('vV')
                if expected_version and release_tag:
                    if self._version_tuple(release_tag) != self._version_tuple(expected_version):
                        fail_update(f"Update aborted: release tag ({release_tag}) does not match expected version ({expected_version}).")
                        return
                # Prefer full installer updates on Windows for reliability and complete file replacement.
                if platform.system() == "Windows":
                    installer_asset = self._pick_installer_asset(release_data, expected_version=expected_version)
                    if installer_asset:
                        self._installer_fallback_in_progress = True
                        self._root.after(0, lambda: self._update_overlay_set_status("Downloading full installer update..."))
                        self._download_and_run_installer_fallback(installer_asset)
                        return
                def _is_runtime_exe_asset(a):
                    name = (a.get('name') or '').strip().lower()
                    if not name.endswith('.exe'):
                        return False
                    bad_markers = ("setup", "installer", "updater", "signtool", "portable", "unins", "uninstall")
                    if any(m in name for m in bad_markers):
                        return False
                    # In-app updater only supports runtime app executables.
                    if name == current_name or name == "autobe.exe":
                        return True
                    if "autobe" in name:
                        return True
                    return False
                def _asset_score(a):
                    """Higher score = better candidate for in-app exe replacement."""
                    name = (a.get('name') or '').strip().lower()
                    if not _is_runtime_exe_asset(a):
                        return -1
                    score = 0
                    if name == current_name:
                        score += 1000
                    if "autobe" in name:
                        score += 200
                    # Prefer larger binaries (one-file builds are typically larger than helper exes).
                    try:
                        size = int(a.get('size') or 0)
                    except Exception:
                        size = 0
                    score += min(size // (1024 * 1024), 200)  # up to +200 for size
                    return score
                candidates = [a for a in assets if _is_runtime_exe_asset(a)]
                ranked = sorted(candidates, key=_asset_score, reverse=True)
                exe_asset = ranked[0] if ranked and _asset_score(ranked[0]) >= 0 else None
                if not exe_asset:
                    fail_update(_("update.not_ready_no_file"))
                    return
                # Private repos: MUST use asset API url with token. browser_download_url returns 404 with token.
                if GITHUB_TOKEN:
                    download_url = exe_asset.get('url')
                    if not download_url and exe_asset.get('id'):
                        download_url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/assets/{exe_asset['id']}"
                else:
                    download_url = exe_asset.get('browser_download_url')
                if not download_url:
                    fail_update(_("update.not_ready"))
                    return
                if not current_exe.lower().endswith('.exe'):
                    fail_update(_("update.manual_only"))
                    return
                td = _tempfile.gettempdir()
                new_exe = _os.path.join(td, "AutoBE_update.exe")
                headers = {"Accept": "application/octet-stream"}
                if GITHUB_TOKEN:
                    headers["Authorization"] = f"token {GITHUB_TOKEN}"
                _last_download_url = download_url
                r = _requests.get(download_url, headers=headers, timeout=60, stream=True, allow_redirects=True)
                r.raise_for_status()
                with open(new_exe, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                # Basic integrity checks to avoid replacing with a broken/partial file.
                downloaded_size = _os.path.getsize(new_exe) if _os.path.exists(new_exe) else 0
                expected_size = int(exe_asset.get('size') or 0)
                if downloaded_size <= 0:
                    fail_update("Update failed: downloaded file is empty.")
                    return
                if expected_size > 0 and downloaded_size != expected_size:
                    fail_update(f"Update failed: file size mismatch (expected {expected_size}, got {downloaded_size}).")
                    return
                if downloaded_size < 2 * 1024 * 1024:
                    fail_update("Update failed: downloaded .exe is unexpectedly small. Release asset may be incorrect.")
                    return
                # Hard guard: ensure downloaded EXE version matches the expected release version.
                if expected_version:
                    downloaded_ver = self._get_windows_exe_version(new_exe)
                    if not downloaded_ver:
                        fail_update(
                            "Update failed: could not verify downloaded EXE version metadata. "
                            "Rebuild and upload a versioned AutoBE.exe asset."
                        )
                        return
                    if self._version_tuple(downloaded_ver) != self._version_tuple(expected_version):
                        fail_update(
                            f"Update aborted: downloaded EXE version ({downloaded_ver}) does not match expected "
                            f"version ({expected_version})."
                        )
                        return
                # Hard guard: block Python 3.13 runtime updates to prevent known python313.dll startup failures.
                try:
                    with open(new_exe, "rb") as _bf:
                        _blob = _bf.read()
                    if b"python313.dll" in _blob.lower():
                        fail_update(
                            "Update blocked: release EXE contains Python 3.13 runtime (python313.dll), "
                            "which is known to fail on some user PCs. Publish a Python 3.12 build."
                        )
                        return
                except Exception:
                    pass
                self._root.after(0, lambda: self._update_overlay_set_status(_("update.installing")))
                self._root.after(500, lambda: self._run_updater_batch(new_exe, current_exe))
            except Exception as e:
                log_error(e)
                try:
                    used_api = "api.github.com" in str(_last_download_url)
                except NameError:
                    used_api = False
                hint = "\n\n(Using API. If 404: check token has repo scope; or rebuild this exe from current AutoBE.py.)" if used_api else "\n\n(Rebuild this exe from current AutoBE.py so private-repo update works.)"
                fail_update(f"Update failed: {str(e)}{hint}")

        threading.Thread(target=do_download, daemon=True).start()

    def _run_updater_batch(self, new_exe, current_exe):
        """Write and run the batch that replaces exe and restarts. Then exit."""
        try:
            td = _tempfile.gettempdir()
            batch = _os.path.join(td, "AutoBE_updater.bat")
            marker_file = _os.path.join(td, f"AutoBE_update_ok_{int(_time.time())}_{_random.randint(1000, 9999)}.marker")
            result_file = _os.path.join(td, f"AutoBE_update_result_{int(_time.time())}_{_random.randint(1000, 9999)}.txt")
            fallback_result_file = _get_update_result_fallback_path()
            with open(batch, 'w') as f:
                f.write('@echo off\n')
                f.write('setlocal EnableExtensions\n')
                f.write('set "SRC=' + new_exe.replace('"', '""') + '"\n')
                f.write('set "DST=' + current_exe.replace('"', '""') + '"\n')
                f.write('set "BAK=' + (current_exe + ".preupdate.bak").replace('"', '""') + '"\n')
                f.write('set "MARK=' + marker_file.replace('"', '""') + '"\n')
                f.write('set "RES=' + result_file.replace('"', '""') + '"\n')
                f.write('set "RESP=' + fallback_result_file.replace('"', '""') + '"\n')
                f.write('del "%MARK%" 2>nul\n')
                f.write('del "%RES%" 2>nul\n')
                f.write('del "%RESP%" 2>nul\n')
                f.write('copy /y "%DST%" "%BAK%" >nul\n')
                f.write('set "COPIED_OK=0"\n')
                f.write('for /L %%I in (1,1,8) do (\n')
                f.write('    timeout /t 1 /nobreak >nul\n')
                f.write('    copy /y "%SRC%" "%DST%" >nul\n')
                f.write('    if errorlevel 1 (\n')
                f.write('        rem copy failed this round, retry\n')
                f.write('    ) else (\n')
                f.write('        for %%S in ("%SRC%") do set "SRC_SIZE=%%~zS"\n')
                f.write('        for %%D in ("%DST%") do set "DST_SIZE=%%~zD"\n')
                f.write('        if "%SRC_SIZE%"=="%DST_SIZE%" (\n')
                f.write('            set "COPIED_OK=1"\n')
                f.write('            goto :copied\n')
                f.write('        )\n')
                f.write('    )\n')
                f.write(')\n')
                f.write(':copied\n')
                f.write('if "%COPIED_OK%"=="1" (\n')
                f.write('    > "%RES%" echo UPDATED_OK\n')
                f.write('    > "%RESP%" echo UPDATED_OK\n')
                f.write('    start "" "%DST%" --post-update-check "%MARK%" --post-update-result "%RES%"\n')
                f.write('    for /L %%J in (1,1,25) do (\n')
                f.write('        timeout /t 1 /nobreak >nul\n')
                f.write('        if exist "%MARK%" goto :healthy\n')
                f.write('    )\n')
                f.write('    goto :rollback\n')
                f.write(') else (\n')
                f.write('    rem Do not run from temp fallback; keep installed path authoritative.\n')
                f.write('    > "%RES%" echo UPDATED_COPY_FAILED\n')
                f.write('    > "%RESP%" echo UPDATED_COPY_FAILED\n')
                f.write('    copy /y "%BAK%" "%DST%" >nul\n')
                f.write('    start "" "%DST%" --post-update-result "%RES%"\n')
                f.write('    goto :cleanup\n')
                f.write(')\n')
                f.write(':healthy\n')
                f.write('del "%MARK%" 2>nul\n')
                f.write('del "%BAK%" 2>nul\n')
                f.write('del "%SRC%" 2>nul\n')
                f.write('goto :cleanup\n')
                f.write(':rollback\n')
                f.write('> "%RES%" echo UPDATED_ROLLBACK\n')
                f.write('> "%RESP%" echo UPDATED_ROLLBACK\n')
                f.write('copy /y "%BAK%" "%DST%" >nul\n')
                f.write('set "BAK_IS_313=0"\n')
                f.write('findstr /M /I /C:"python313.dll" "%BAK%" >nul 2>nul && set "BAK_IS_313=1"\n')
                f.write('if "%BAK_IS_313%"=="1" (\n')
                f.write('    rem Backup requires py313 runtime; skip auto-launch to avoid a second DLL error dialog.\n')
                f.write('    goto :cleanup\n')
                f.write(')\n')
                f.write('start "" "%DST%" --post-update-result "%RES%"\n')
                f.write(':cleanup\n')
                f.write('del "%~f0" 2>nul\n')
            if platform.system() == "Windows":
                # Always request elevation for replacement so update completes consistently on user systems.
                vbs = _os.path.join(td, "AutoBE_updater_elevate.vbs")
                batch_esc = batch.replace('"', '""')
                with open(vbs, 'w') as f:
                    f.write('CreateObject("Shell.Application").ShellExecute "cmd.exe", "/c ""' + batch_esc + '""", "", "runas", 0\n')
                subprocess.Popen(['wscript.exe', '//B', vbs], creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0x08000000))
            else:
                subprocess.Popen(['sh', '-c', f'sleep 2; cp "{new_exe}" "{current_exe}" && "{current_exe}" &'], creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0x08000000) if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0)
            sys.exit(0)
        except Exception as e:
            log_error(e)
            self._show_update_error(f"Install failed: {str(e)}")

    def _pick_installer_asset(self, release_data, expected_version=None):
        """Select installer asset (.exe setup) from release assets."""
        assets = (release_data or {}).get("assets") or []
        ver_norm = str(expected_version or "").strip().lstrip("vV")

        def _score(a):
            name = str((a or {}).get("name") or "").strip().lower()
            if not name.endswith(".exe"):
                return -1
            if not any(k in name for k in ("setup", "installer")):
                return -1
            score = 0
            if "autobe" in name:
                score += 200
            if "setup" in name:
                score += 120
            if "installer" in name:
                score += 80
            if ver_norm and ver_norm in name:
                score += 300
            try:
                score += min(int((a or {}).get("size") or 0) // (1024 * 1024), 150)
            except Exception:
                pass
            return score

        ranked = sorted(assets, key=_score, reverse=True)
        return ranked[0] if ranked and _score(ranked[0]) >= 0 else None

    def _offer_installer_fallback_update(self, release_data, expected_version, fail_message):
        """Offer installer-based fallback when in-place EXE update is blocked."""
        try:
            if getattr(self, "_installer_fallback_in_progress", False):
                return
            installer_asset = self._pick_installer_asset(release_data, expected_version=expected_version)
            if not installer_asset:
                self._show_update_error(fail_message)
                return
            ask = _messagebox.askyesno(
                _("update.failed"),
                f"{fail_message}\n\n"
                "AutoBE can download and run the installer update automatically instead.\n"
                "Do you want to continue with installer fallback?",
            )
            if not ask:
                self._show_update_error(fail_message)
                return
            self._installer_fallback_in_progress = True
            self._show_update_overlay_ui("Downloading installer fallback...")
            threading.Thread(
                target=self._download_and_run_installer_fallback,
                args=(installer_asset,),
                daemon=True,
            ).start()
        except Exception as e:
            log_error(e)
            self._show_update_error(fail_message)

    def _download_and_run_installer_fallback(self, installer_asset):
        """Download installer asset and run elevated in-place upgrade."""
        try:
            if GITHUB_TOKEN:
                download_url = installer_asset.get("url")
                if not download_url and installer_asset.get("id"):
                    download_url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/assets/{installer_asset['id']}"
            else:
                download_url = installer_asset.get("browser_download_url")
            if not download_url:
                raise RuntimeError("Installer fallback failed: no installer download URL.")
            headers = {"Accept": "application/octet-stream"}
            if GITHUB_TOKEN:
                headers["Authorization"] = f"token {GITHUB_TOKEN}"
            td = _tempfile.gettempdir()
            installer_path = _os.path.join(td, "AutoBE_update_setup.exe")
            r = _requests.get(download_url, headers=headers, timeout=90, stream=True, allow_redirects=True)
            r.raise_for_status()
            with open(installer_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            got = _os.path.getsize(installer_path) if _os.path.exists(installer_path) else 0
            exp = int(installer_asset.get("size") or 0)
            if got <= 0:
                raise RuntimeError("Installer fallback failed: downloaded installer is empty.")
            if exp > 0 and got != exp:
                raise RuntimeError(f"Installer fallback failed: size mismatch (expected {exp}, got {got}).")
            self._root.after(0, lambda: self._update_overlay_set_status("Launching installer update..."))
            self._root.after(300, lambda: self._run_installer_fallback_batch(installer_path, sys.executable))
        except Exception as e:
            log_error(e)
            self._installer_fallback_in_progress = False
            self._root.after(0, lambda: self._show_update_error(f"Installer fallback failed: {str(e)}"))

    def _run_installer_fallback_batch(self, installer_exe, current_exe):
        """Run installer as elevated upgrade, then relaunch app."""
        try:
            td = _tempfile.gettempdir()
            batch = _os.path.join(td, "AutoBE_installer_update.bat")
            with open(batch, "w", encoding="utf-8") as f:
                f.write("@echo off\n")
                f.write("setlocal EnableExtensions\n")
                f.write('set "INS=' + installer_exe.replace('"', '""') + '"\n')
                f.write('set "APP=' + current_exe.replace('"', '""') + '"\n')
                f.write("timeout /t 1 /nobreak >nul\n")
                f.write('start "" /wait "%INS%" /SP- /NORESTART /CLOSEAPPLICATIONS\n')
                f.write('if exist "%APP%" start "" "%APP%"\n')
                f.write('del "%INS%" 2>nul\n')
                f.write('del "%~f0" 2>nul\n')
            if platform.system() == "Windows":
                vbs = _os.path.join(td, "AutoBE_installer_update_elevate.vbs")
                batch_esc = batch.replace('"', '""')
                with open(vbs, "w", encoding="utf-8") as f:
                    f.write('CreateObject("Shell.Application").ShellExecute "cmd.exe", "/c ""' + batch_esc + '""", "", "runas", 0\n')
                subprocess.Popen(["wscript.exe", "//B", vbs], creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000))
            else:
                subprocess.Popen(["sh", "-c", f'"{installer_exe}" &'], creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000) if hasattr(subprocess, "CREATE_NO_WINDOW") else 0)
            sys.exit(0)
        except Exception as e:
            log_error(e)
            self._installer_fallback_in_progress = False
            self._show_update_error(f"Installer launch failed: {str(e)}")

    def _show_update_error(self, message):
        """Show themed error on update overlay with Close button. No browser."""
        self._update_overlay.grid()
        self._update_overlay.lift()
        for w in self._update_overlay.winfo_children():
            w.destroy()
        self._update_overlay.grid_columnconfigure(0, weight=1)
        self._update_overlay.grid_rowconfigure(0, weight=1)
        center = _tk.Frame(self._update_overlay, bg='#000000')
        center.place(relx=0.5, rely=0.5, anchor='center')
        _tk.Label(center, text=_("update.failed"), bg='#000000', fg='#ef4444', font=('Segoe UI', 18, 'bold')).pack(pady=(0, 16))
        _tk.Label(center, text=message, bg='#000000', fg='#e5e7eb', font=('Segoe UI', 10), justify='center', wraplength=360).pack(pady=(0, 24))
        def close():
            self._update_overlay.grid_remove()
        _tk.Button(center, text=_("common.close"), command=close, bg='#9333ea', fg='#FFFFFF', font=('Segoe UI', 11, 'bold'), relief='flat', cursor='hand2', activebackground='#a855f7', padx=32, pady=10).pack()

    def _check_activation(self):
        _hwid = self._generate_hwid()

        # Clear local cache files on reinstall to fix false bans
        self._clear_local_cache_files()

        try:
            # version.txt line 1 = minimum version allowed to run; line 2 = latest version for Check for updates.
            _version_text = self._fetch_github_file("version.txt")
            if _version_text:
                try:
                    _min_allowed = _version_text.strip().splitlines()[0].strip()
                    if self._version_tuple(APP_VERSION) < self._version_tuple(_min_allowed):
                        _messagebox.showerror(_("update.update_required_title"), _("update.update_required_msg"))
                        sys.exit()
                except Exception as e:
                    _logging.debug("Version check parse failed: %s", e)
            # If _version_text is None, network failed — skip version check (allow offline use)

            # --- Check blacklist from GitHub (or cached when offline) ---
            blacklist_text = self._fetch_github_file("blacklist.txt")
            if blacklist_text:
                self._save_blacklist_cache(blacklist_text)
                current_blacklist = set(line.strip() for line in blacklist_text.strip().splitlines() if line.strip())
                _hwid_in_block = _hwid in current_blacklist
                # If HWID is NOT in GitHub blacklist but IS in local cache, clear local cache (user was unbanned)
                if not _hwid_in_block:
                    blocked_hashes = self._load_cached_blacklist()
                    if self._block_hash(_hwid) in blocked_hashes:
                        # Clear local cache since user was unbanned on GitHub
                        try:
                            _os.remove(self._get_blacklist_cache_path())
                            _logging.info("Cleared local blacklist cache (HWID removed from GitHub)")
                        except Exception:
                            pass
            else:
                blocked_hashes = self._load_cached_blacklist()
                _hwid_in_block = self._block_hash(_hwid) in blocked_hashes
            if _hwid_in_block:
                # Show ban screen - ensure root is visible first
                if self._is_root_alive():
                    try:
                        self._root.deiconify()
                        self._root.update_idletasks()
                    except:
                        pass
                    self._root.after(100, lambda: self._show_ban_screen("You have been banned from using AutoBE."))
                else:
                    _messagebox.showerror(_("activation.denied"), _("msg.banned"))
                    sys.exit()
                return

            # --- Check for spoofed system / VM (Windows, Linux, macOS) ---
            # DISABLED: Spoofing detection causing false bans - too aggressive
            # spoofing_detected = self._detect_spoofing(_hwid)
            # if spoofing_detected:
            #     # Auto-add to GitHub blacklist + local cache (only when 2+ flags; reduces false positives)
            #     try:
            #         self._append_to_blacklist(_hwid)
            #     except Exception as e:
            #         log_error(f"Failed to add spoofer to blacklist: {e}")
            #     self._append_to_blacklist_cache(_hwid)
            #     denied_message = "Spoofed hardware detected.\nAccess denied."
            #     if self._is_root_alive():
            #         try:
            #             self._root.deiconify()
            #             self._root.update_idletasks()
            #         except Exception:
            #             pass
            #         self._root.after(100, lambda: self._show_denied_screen(denied_message))
            #     else:
            #         _messagebox.showerror(_("msg.spoofer_detected"), denied_message)
            #         sys.exit()

            # --- Check HWID whitelist from GitHub (we only check if *this* device's HWID is in it; never show or store other users' HWIDs) ---
            hwid_text = self._fetch_github_file("hwid_address.txt")
            if hwid_text:
                try:
                    valid_hwids = [h.strip() for h in hwid_text.splitlines() if h.strip()]
                    if _hwid in valid_hwids:
                        # Device binding: same HWID must be from same physical machine (detect HWID spoofing)
                        # DISABLED: Fingerprint check causing false bans - too aggressive
                        # hwid_h = self._block_hash(_hwid)
                        # current_fp = self._get_device_fingerprint()
                        # stored_fp = self._get_stored_fingerprint(hwid_h)
                        # if stored_fp is not None and stored_fp != current_fp:
                        #     self._deny_and_blacklist_spoofed_hwid(_hwid)
                        #     return
                        self._save_verified_hwid(_hwid)
                        # self._save_fingerprint_for_hwid(hwid_h, current_fp)
                        if self._is_root_alive():
                            self._root.after(0, self._unlock_application)
                        return
                except Exception as e:
                    _logging.debug("HWID whitelist parse failed: %s", e)

            # --- Offline (could not reach GitHub): only allow if *this* device's HWID was already verified on this machine (must have activated with WiFi first) ---
            if hwid_text is None:
                verified_hashes = self._load_verified_hwids()
                if self._block_hash(_hwid) in verified_hashes:
                    # Device binding: fingerprint must match the device that first activated this HWID
                    # DISABLED: Fingerprint check causing false bans - too aggressive
                    # hwid_h = self._block_hash(_hwid)
                    # current_fp = self._get_device_fingerprint()
                    # stored_fp = self._get_stored_fingerprint(hwid_h)
                    # if stored_fp is not None and stored_fp != current_fp:
                    #     self._deny_and_blacklist_spoofed_hwid(_hwid)
                    #     return
                    if self._is_root_alive():
                        self._root.after(0, self._unlock_application)
                    return
                # Not verified — require internet to verify
                if self._is_root_alive():
                    self._root.after(0, lambda: self._show_activation_window(offline=True))
                return

            # Online but not in whitelist — sync local memory: remove this device from verified so they can't use offline either; then show activation
            self._remove_verified_hwid(_hwid)
            if self._is_root_alive():
                self._root.after(0, self._show_activation_window)
                
        except Exception as e:
            _logging.error("Activation failed", exc_info=e)
            # Show activation window as fallback
            if self._is_root_alive():
                self._root.after(0, self._show_activation_window)

    def _show_ban_screen(self, ban_message):
        """Show ban screen overlay only when the player is found in the blacklist."""
        if not self._is_root_alive():
            return
        
        # Clear any existing widgets in ban overlay
        for widget in self._ban_overlay.winfo_children():
            widget.destroy()
        
        # Configure ban overlay
        self._ban_overlay.columnconfigure(0, weight=1)
        self._ban_overlay.rowconfigure(0, weight=1)
        
        # Main container
        container = _tk.Frame(self._ban_overlay, bg='#000000')
        container.grid(row=0, column=0, sticky="nsew")
        container.columnconfigure(0, weight=1)
        container.rowconfigure(1, weight=1)
        
        # Ban icon/header (using text as icon)
        icon_frame = _tk.Frame(container, bg='#000000')
        icon_frame.grid(row=0, column=0, pady=(80, 20))
        
        ban_icon = _tk.Label(
            icon_frame,
            text="🚫",
            bg='#000000',
            fg='#FF0000',
            font=("Segoe UI", 72, "bold")
        )
        ban_icon.pack()
        
        # Ban title
        title_label = _tk.Label(
            container,
            text=_("activation.denied"),
            bg='#000000',
            fg='#FF0000',
            font=("Segoe UI", 32, "bold")
        )
        title_label.grid(row=1, column=0, pady=(0, 20))
        
        # Ban message
        message_label = _tk.Label(
            container,
            text=ban_message,
            bg='#000000',
            fg='#FFFFFF',
            font=("Segoe UI", 14),
            justify='center',
            wraplength=600
        )
        message_label.grid(row=2, column=0, pady=(0, 30))
        
        # Additional info
        info_label = _tk.Label(
            container,
            text=_("activation.device_denied"),
            bg='#000000',
            fg='#888888',
            font=("Segoe UI", 11),
            justify='center'
        )
        info_label.grid(row=3, column=0, pady=(0, 40))
        
        # Close button
        close_button = _tk.Button(
            container,
            text=_("common.close"),
            command=self._root.destroy,
            bg='#1a1a1a',
            fg='#FFFFFF',
            font=("Segoe UI", 12, "bold"),
            relief='flat',
            cursor='hand2',
            activebackground='#2a2a2a',
            activeforeground='#FFFFFF',
            padx=40,
            pady=10,
            borderwidth=1,
            highlightthickness=1,
            highlightbackground='#FF0000',
            highlightcolor='#FF0000'
        )
        close_button.grid(row=4, column=0, pady=(0, 50))
        
        # Ensure root window is visible and on top
        try:
            self._root.deiconify()
            self._root.lift()
            self._root.focus_force()
            self._root.update_idletasks()
        except:
            pass
        
        # Show ban overlay (on top of everything)
        self._ban_overlay.tkraise()
        self._ban_overlay.grid()
        self._ban_overlay.update_idletasks()
        
        # Prevent window from being closed during ban screen
        self._root.protocol("WM_DELETE_WINDOW", lambda: None)
        
        # Auto-close after 10 seconds
        self._root.after(10000, self._root.destroy)

    def _show_denied_screen(self, message):
        """Show access-denied overlay (e.g. spoofing). Not the ban screen; ban is only for blacklist."""
        if not self._is_root_alive():
            return
        
        for widget in self._ban_overlay.winfo_children():
            widget.destroy()
        self._ban_overlay.columnconfigure(0, weight=1)
        self._ban_overlay.rowconfigure(0, weight=1)
        container = _tk.Frame(self._ban_overlay, bg='#000000')
        container.grid(row=0, column=0, sticky="nsew")
        container.columnconfigure(0, weight=1)
        container.rowconfigure(1, weight=1)
        icon_frame = _tk.Frame(container, bg='#000000')
        icon_frame.grid(row=0, column=0, pady=(80, 20))
        _tk.Label(icon_frame, text="⚠", bg='#000000', fg='#CC6600', font=("Segoe UI", 72, "bold")).pack()
        title = _("activation.access_denied") if _("activation.access_denied") != "activation.access_denied" else "Access denied"
        _tk.Label(container, text=title, bg='#000000', fg='#CC6600', font=("Segoe UI", 32, "bold")).grid(row=1, column=0, pady=(0, 20))
        _tk.Label(container, text=message, bg='#000000', fg='#FFFFFF', font=("Segoe UI", 14), justify='center', wraplength=600).grid(row=2, column=0, pady=(0, 30))
        _tk.Label(container, text=_("activation.device_denied"), bg='#000000', fg='#888888', font=("Segoe UI", 11), justify='center').grid(row=3, column=0, pady=(0, 40))
        close_btn = _tk.Button(container, text=_("common.close"), command=self._root.destroy, bg='#1a1a1a', fg='#FFFFFF', font=("Segoe UI", 12, "bold"), relief='flat', cursor='hand2', activebackground='#2a2a2a', activeforeground='#FFFFFF', padx=40, pady=10, borderwidth=1, highlightthickness=1, highlightbackground='#CC6600', highlightcolor='#CC6600')
        close_btn.grid(row=4, column=0, pady=(0, 50))
        try:
            self._root.deiconify()
            self._root.lift()
            self._root.focus_force()
            self._root.update_idletasks()
        except Exception:
            pass
        self._ban_overlay.tkraise()
        self._ban_overlay.grid()
        self._ban_overlay.update_idletasks()
        self._root.protocol("WM_DELETE_WINDOW", lambda: None)
        self._root.after(10000, self._root.destroy)
    
    def _create_activation_overlay(self):
        """Create the activation overlay UI in the main window."""
        if not self._is_root_alive():
            return
        
        # Ensure root is visible
        try:
            self._root.deiconify()
        except:
            pass
            
        # Clear any existing widgets in the overlay
        for widget in self._activation_overlay.winfo_children():
            widget.destroy()
        
        # Create centered container with modern styling
        center_frame = _tk.Frame(self._activation_overlay, bg='#000000')
        center_frame.place(relx=0.5, rely=0.5, anchor='center')
        
        # Modern lock icon with subtle glow effect
        lock_label = _tk.Label(
            center_frame,
            text="🔒",
            bg='#000000',
            fg='#A50CAC',
            font=("Segoe UI", 56, "bold")
        )
        lock_label.pack(pady=(0, 40))
        
        # Instructions with modern typography
        instruction_label = _tk.Label(
            center_frame,
            text=_("activation.enter_key_title"),
            bg='#000000',
            fg='#FFFFFF',
            font=("Segoe UI", 16, "normal")
        )
        instruction_label.pack(pady=(0, 25))
        if getattr(self, '_activation_offline', False):
            offline_label = _tk.Label(
                center_frame,
                text=_("activation.offline_verify") if _("activation.offline_verify") != "activation.offline_verify" else "Connect to the internet to verify.",
                bg='#000000',
                fg='#A50CAC',
                font=("Segoe UI", 12, "normal")
            )
            offline_label.pack(pady=(0, 15))
        
        # Modern entry field - pure black, no borders
        self._activation_entry = _tk.Entry(
            center_frame,
            width=45,
            bg='#000000',
            fg='#FFFFFF',
            font=("Segoe UI", 13),
            insertbackground='#A50CAC',
            relief=_tk.FLAT,
            bd=0,
            highlightthickness=0
        )
        self._activation_entry.pack(pady=10, padx=20, ipady=8)
        self._activation_entry.focus()
        
        # Bind Enter key to submit
        self._activation_entry.bind('<Return>', lambda e: self._submit_activation_key())
        
        # Modern submit button with hover effect
        submit_btn = _tk.Button(
            center_frame,
            text=_("activation.activate"),
            command=self._submit_activation_key,
            bg='#A50CAC',
            fg='#FFFFFF',
            font=("Segoe UI", 13, "bold"),
            relief=_tk.FLAT,
            bd=0,
            cursor="hand2",
            activebackground='#8B0A9C',
            activeforeground='#FFFFFF',
            padx=40,
            pady=12,
            highlightthickness=0
        )
        submit_btn.pack(pady=(20, 10))
        
        # Error label with modern styling
        self._activation_error_label = _tk.Label(
            center_frame,
            text="",
            bg='#000000',
            fg='#FF6B6B',
            font=("Segoe UI", 11)
        )
        self._activation_error_label.pack(pady=(5, 0))
        
        # Show the overlay
        self._activation_overlay.tkraise()
    
    def _show_loading_animation(self, wait_seconds=120):
        """Show RGB loading animation while processing activation."""
        if not self._is_root_alive():
            return
        
        # Set loading state to prevent closing
        self._is_loading = True
            
        # Clear any existing widgets in the overlay
        for widget in self._activation_overlay.winfo_children():
            widget.destroy()
        
        # Create centered container
        center_frame = _tk.Frame(self._activation_overlay, bg='#000000')
        center_frame.place(relx=0.5, rely=0.5, anchor='center')
        
        # Title
        title_label = _tk.Label(
            center_frame,
            text=_("activation.processing"),
            bg='#000000',
            fg='#FFFFFF',
            font=("Segoe UI", 20, "bold")
        )
        title_label.pack(pady=(0, 40))
        
        # Loading spinner container
        spinner_frame = _tk.Frame(center_frame, bg='#000000')
        spinner_frame.pack(pady=20)
        
        # Create multiple spinning circles for RGB effect
        self._loading_dots = []
        dot_colors = ['#FF0000', '#00FF00', '#0000FF', '#FFFF00', '#FF00FF', '#00FFFF']
        for i in range(6):
            dot = _tk.Label(
                spinner_frame,
                text="●",
                bg='#000000',
                fg=dot_colors[i],
                font=("Segoe UI", 24, "bold")
            )
            dot.pack(side=_tk.LEFT, padx=5)
            self._loading_dots.append(dot)
        
        # Status text
        self._loading_status_label = _tk.Label(
            center_frame,
            text=_("activation.syncing"),
            bg='#000000',
            fg='#A50CAC',
            font=("Segoe UI", 12)
        )
        self._loading_status_label.pack(pady=30)
        
        # Progress counter
        self._loading_progress_label = _tk.Label(
            center_frame,
            text="",
            bg='#000000',
            fg='#CCCCCC',
            font=("Segoe UI", 11)
        )
        self._loading_progress_label.pack(pady=10)
        
        # Store animation state
        self._loading_animation_step = 0
        self._loading_wait_remaining = wait_seconds
        self._loading_animation_id = None
        
        # Start animation
        self._loading_status_messages = [
            _("activation.syncing"),
            _("activation.processing_key"),
            _("activation.updating_db"),
            _("activation.finalizing"),
            _("activation.almost_done")
        ]
        self._loading_status_index = 0
        
        # Update progress label
        self._loading_progress_label.config(text=_f("activation.please_wait_seconds", seconds=wait_seconds))
        
        # Start the RGB animation
        self._animate_loading_rgb()
        
        # Start countdown
        self._loading_countdown()
