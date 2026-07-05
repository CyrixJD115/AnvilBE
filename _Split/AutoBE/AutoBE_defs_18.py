def _run_splash_then_app():
    """Show opening.gif splash from locales for a minimum time, then start the main app. Works for all users (verified and unverified)."""
    _init_translations()
    # Don't call basicConfig here - logging is already configured with the proper file path at module level
    # Calling basicConfig without filename would default to current directory (Program Files when installed as exe)
    # which causes permission errors when not run as admin

    splash_root = _tk.Tk()
    splash_root.withdraw()
    splash_root.configure(bg='#000000')
    splash_root.overrideredirect(True)
    splash_root.attributes('-topmost', True)

    gif_path = None
    for name in ('opening.gif', 'open.gif'):
        p = _os.path.join(_LOCALE_DIR, name)
        if _os.path.isfile(p):
            gif_path = p
            break

    splash_frames = []
    frame_delay_ms = 50
    splash_w, splash_h = 400, 300
    MAX_SPLASH_W, MAX_SPLASH_H = 900, 700  # same max size as AutoBE window

    if gif_path and _PIL_AVAILABLE and _PIL_Image is not None and _PIL_ImageTk is not None:
        try:
            img = _PIL_Image.open(gif_path)
            w, h = img.size
            if w > MAX_SPLASH_W or h > MAX_SPLASH_H:
                r = min(MAX_SPLASH_W / w, MAX_SPLASH_H / h)
                splash_w, splash_h = int(w * r), int(h * r)
            else:
                splash_w, splash_h = w, h
            thumb_resample = getattr(_PIL_Image.Resampling, 'LANCZOS', None) or getattr(_PIL_Image, 'LANCZOS', 1)
            try:
                n = 0
                while True:
                    img.seek(n)
                    f = img.copy()
                    if f.mode in ('RGBA', 'LA', 'P'):
                        if f.mode == 'P' and 'transparency' in img.info:
                            f = f.convert('RGBA')
                        bg = _PIL_Image.new('RGB', f.size, (0, 0, 0))
                        if f.mode in ('RGBA', 'LA'):
                            bg.paste(f, mask=f.split()[-1])
                        else:
                            bg.paste(f)
                        f = bg
                    elif f.mode != 'RGB':
                        f = f.convert('RGB')
                    f.thumbnail((splash_w, splash_h), thumb_resample)
                    splash_frames.append(_PIL_ImageTk.PhotoImage(f))
                    n += 1
            except EOFError:
                pass
            if getattr(img, 'info', None) and 'duration' in img.info:
                frame_delay_ms = max(20, min(img.info['duration'], 200))
        except Exception:
            splash_frames = []

    if not splash_frames and gif_path:
        try:
            photo = _tk.PhotoImage(file=gif_path)
            splash_frames.append(photo)
            w, h = photo.width(), photo.height()
            if w > MAX_SPLASH_W or h > MAX_SPLASH_H:
                r = min(MAX_SPLASH_W / w, MAX_SPLASH_H / h)
                splash_w, splash_h = int(w * r), int(h * r)
            else:
                splash_w, splash_h = w, h
        except Exception:
            pass

    screen_w = splash_root.winfo_screenwidth()
    screen_h = splash_root.winfo_screenheight()
    x = max(0, (screen_w - splash_w) // 2)
    y = max(0, (screen_h - splash_h) // 2)
    splash_root.geometry(f'{splash_w}x{splash_h}+{x}+{y}')
    splash_root.resizable(False, False)

    # Pack dot bar first so it stays fixed at the bottom; then GIF fills the rest above it
    DOT_COLORS = ('#0d0d0d', '#1a0a2e', '#3d1a5c', '#9333ea', '#3d1a5c', '#1a0a2e')
    NUM_DOTS = 12
    dot_bar = _tk.Frame(splash_root, bg='#000000', height=56)
    dot_bar.pack(side='bottom', fill='x', padx=0, pady=0)
    dot_bar.pack_propagate(False)
    dot_inner = _tk.Frame(dot_bar, bg='#000000')
    dot_inner.pack(expand=True)
    dot_labels = []
    for i in range(NUM_DOTS):
        lb = _tk.Label(dot_inner, text='\u2022', bg='#000000', fg=DOT_COLORS[0], font=('Segoe UI', 24, 'bold'), relief='flat')
        lb.pack(side='left', padx=5)
        dot_labels.append(lb)
    dot_phase = [0]
    DOT_ANIM_MS = 90
    splash_closed = [False]
    tick_dots_after_id = [None]
    show_frame_after_id = [None]

    def tick_dots():
        if splash_closed[0]:
            return
        try:
            if not splash_root.winfo_exists():
                return
        except Exception:
            return
        dot_phase[0] = (dot_phase[0] + 1) % len(DOT_COLORS)
        for i, lb in enumerate(dot_labels):
            idx = (dot_phase[0] + i) % len(DOT_COLORS)
            c = DOT_COLORS[idx]
            lb.configure(fg=c)
        if not splash_closed[0]:
            try:
                tick_dots_after_id[0] = splash_root.after(DOT_ANIM_MS, tick_dots)
            except Exception:
                pass

    tick_dots_after_id[0] = splash_root.after(DOT_ANIM_MS, tick_dots)

    label = _tk.Label(splash_root, image=None, bg='#000000')
    label.pack(side='top', fill='both', expand=True)
    splash_current = [0]
    splash_refs = [splash_frames]

    def show_frame():
        if splash_closed[0] or not splash_refs[0]:
            return
        try:
            if not splash_root.winfo_exists():
                return
        except Exception:
            return
        idx = splash_current[0] % len(splash_refs[0])
        label.configure(image=splash_refs[0][idx])
        label.image = splash_refs[0][idx]
        splash_current[0] += 1
        if not splash_closed[0]:
            try:
                show_frame_after_id[0] = splash_root.after(frame_delay_ms, show_frame)
            except Exception:
                pass

    if splash_frames:
        label.configure(image=splash_frames[0])
        label.image = splash_frames[0]
        show_frame_after_id[0] = splash_root.after(frame_delay_ms, show_frame)
    else:
        label.configure(text='Loading...', fg='#9333ea', font=('Segoe UI', 16, 'bold'))

    splash_root.deiconify()
    splash_root.update_idletasks()
    # Re-hide console in case it appears when Tk or py launcher creates it (cancel these before closing splash)
    console_hide_after_ids = []
    for _ms in (100, 300, 600, 1200):
        console_hide_after_ids.append(splash_root.after(_ms, _hide_console_window))

    SPLASH_MIN_MS = 4200

    def close_splash_and_run_app():
        splash_closed[0] = True
        try:
            try:
                if tick_dots_after_id[0] is not None:
                    splash_root.after_cancel(tick_dots_after_id[0])
                    tick_dots_after_id[0] = None
                if show_frame_after_id[0] is not None:
                    splash_root.after_cancel(show_frame_after_id[0])
                    show_frame_after_id[0] = None
                for _aid in console_hide_after_ids:
                    try:
                        splash_root.after_cancel(_aid)
                    except Exception:
                        pass
            except Exception:
                pass

            try:
                splash_root.destroy()
            except Exception:
                pass

            _root = _tk.Tk()
            _root.withdraw()
            _app = AutoBEApp(_root)
            _signal_post_update_health_if_requested()
            for _ms in (0, 200, 600):
                _root.after(_ms, _hide_console_window)
            _root.mainloop()
        except Exception:
            import traceback
            tb = traceback.format_exc()
            try:
                print(tb, flush=True)
            except Exception:
                pass
            try:
                _messagebox.showerror("AutoBE startup error", tb)
            except Exception:
                pass

    splash_root.after(SPLASH_MIN_MS, close_splash_and_run_app)
    splash_root.mainloop()


def strip_bom(text):
    # Remove Unicode BOM
    if text.startswith('\ufeff'):
        text = text[1:]
    # Remove UTF-8 BOM interpreted as latin-1 (ï»¿)
    if text.startswith('ï»¿'):
        text = text[3:]
    return text

def read_text_file_utf8_strip_bom(path):
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    if text.startswith('\ufeff'):
        text = text[1:]
    return text

def write_text_file_utf8(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def _signal_post_update_health_if_requested():
    """Write post-update marker only after app has initialized successfully."""
    try:
        if "--post-update-check" not in sys.argv:
            return
        _idx = sys.argv.index("--post-update-check")
        if _idx + 1 >= len(sys.argv):
            return
        _marker_path = sys.argv[_idx + 1]
        if not _marker_path:
            return
        with open(_marker_path, "w", encoding="utf-8") as _mf:
            _mf.write("ok\n")
    except Exception:
        pass

def _get_update_result_fallback_path():
    """Stable per-user update result file (survives temp cleanup)."""
    try:
        base = _os.environ.get("LOCALAPPDATA") or _tempfile.gettempdir()
        folder = _os.path.join(base, "AutoBE")
        _os.makedirs(folder, exist_ok=True)
        return _os.path.join(folder, "update_result_pending.txt")
    except Exception:
        return _os.path.join(_tempfile.gettempdir(), "AutoBE_update_result_pending.txt")

def _read_and_remove_update_result_file(path):
    try:
        if not path or not _os.path.isfile(path):
            return None
        with open(path, "r", encoding="utf-8", errors="ignore") as _rf:
            _status = (_rf.read() or "").strip()
        try:
            _os.remove(path)
        except Exception:
            pass
        return _status or None
    except Exception:
        return None

def _consume_post_update_result_arg():
    """Read one-shot updater result marker and return status string."""
    try:
        # Prefer stable fallback file first so manual app restarts still show result.
        _fallback = _read_and_remove_update_result_file(_get_update_result_fallback_path())
        if _fallback:
            return _fallback
        if "--post-update-result" not in sys.argv:
            return None
        _idx = sys.argv.index("--post-update-result")
        if _idx + 1 >= len(sys.argv):
            return None
        _result_path = sys.argv[_idx + 1]
        if not _result_path:
            return None
        if not _os.path.isfile(_result_path):
            # Fallback: updater passed the arg but marker is missing
            # (temp cleanup/AV race). Treat as success so users still
            # get a completion notice instead of silence.
            return "UPDATED_OK"
        return _read_and_remove_update_result_file(_result_path)
    except Exception:
        return None
