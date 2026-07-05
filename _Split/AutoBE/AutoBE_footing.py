
if __name__ == "__main__":
    try:
        try:
            print("Starting AutoBE...", flush=True)
        except Exception:
            pass
        # Only hide console automatically when running as a packaged executable.
        if getattr(sys, "frozen", False):
            _hide_console_window()
        _run_splash_then_app()
    except Exception:
        import traceback
        tb = traceback.format_exc()
        try:
            print(tb, flush=True)
        except Exception:
            pass
        try:
            _messagebox.showerror("AutoBE fatal error", tb)
        except Exception:
            pass
