class AutoBEApp:
    
    def _animate_loading_rgb(self):
        """Animate RGB colors in the loading dots."""
        if not self._is_root_alive() or not hasattr(self, '_loading_dots'):
            return
        
        # RGB color cycling
        step = self._loading_animation_step
        
        for i, dot in enumerate(self._loading_dots):
            # Create RGB color wave effect
            phase = (step + i * 60) % 360
            r = int(127.5 * (1 + math.sin(math.radians(phase))))
            g = int(127.5 * (1 + math.sin(math.radians(phase + 120))))
            b = int(127.5 * (1 + math.sin(math.radians(phase + 240))))
            
            color = f"#{r:02x}{g:02x}{b:02x}"
            dot.config(fg=color)
        
        # Update status message periodically
        if step % 30 == 0 and hasattr(self, '_loading_status_label'):
            self._loading_status_label.config(
                text=self._loading_status_messages[self._loading_status_index % len(self._loading_status_messages)]
            )
            self._loading_status_index += 1
        
        self._loading_animation_step += 5
        self._loading_animation_id = self._root.after(50, self._animate_loading_rgb)
    
    def _loading_countdown(self):
        """Countdown timer for loading."""
        if not self._is_root_alive() or not hasattr(self, '_loading_wait_remaining'):
            return
        
        if self._loading_wait_remaining > 0:
            minutes = self._loading_wait_remaining // 60
            seconds = self._loading_wait_remaining % 60
            if minutes > 0:
                time_text = _f("activation.please_wait_min_sec", minutes=minutes, seconds=seconds)
            else:
                time_text = _f("activation.please_wait_sec", seconds=seconds)
            
            if hasattr(self, '_loading_progress_label'):
                self._loading_progress_label.config(text=time_text)
            
            self._loading_wait_remaining -= 1
            self._root.after(1000, self._loading_countdown)
        else:
            # Stop animation and unlock
            if hasattr(self, '_loading_animation_id') and self._loading_animation_id:
                self._root.after_cancel(self._loading_animation_id)
            
            # Clean up loading state
            if hasattr(self, '_loading_dots'):
                del self._loading_dots
            if hasattr(self, '_loading_animation_step'):
                del self._loading_animation_step
            
            # Re-enable window closing
            self._is_loading = False
            
            # Unlock the application
            self._unlock_application()
        
    def _show_activation_window(self, offline=False):
        """Show activation overlay in the main window. If offline=True, show message that internet is required to verify."""
        if not self._is_root_alive():
            return
        
        self._activation_offline = bool(offline)
        # Ensure root window is visible (in case it was withdrawn)
        self._root.deiconify()
        self._root.lift()
        self._root.focus_force()
        self._root.update_idletasks()
        self._root.update()
        
        # Ensure overlay is visible and on top
        self._activation_overlay.grid()
        self._activation_overlay.tkraise()
        
        # Hide notebook if it's visible
        self.notebook.grid_remove()
        
        self._create_activation_overlay()
        
        # Force update after creating overlay
        self._root.update_idletasks()
        self._root.update()
        
        _logging.debug('Activation overlay displayed.')
    
    def _submit_activation_key(self):
        """Handle activation key submission."""
        if not hasattr(self, '_activation_entry'):
            return
            
        _key = self._activation_entry.get().strip()

        if not _key:
            if hasattr(self, '_activation_error_label'):
                self._activation_error_label.config(text=_("activation.enter_key_error"))
            return

        _url_keys = "https://raw.githubusercontent.com/FrostyHostMC/AutoBE/main/keys.csv"
        _headers = {
            "Authorization": f"token {GITHUB_TOKEN}"
        }

        try:
            # Clear error message
            if hasattr(self, '_activation_error_label'):
                self._activation_error_label.config(text="")
            
            # Fetch the current list of valid keys using the helper function
            keys_text = self._fetch_github_file("keys.csv")
            if keys_text is None:
                if hasattr(self, '_activation_error_label'):
                    self._activation_error_label.config(text=_("msg.connection_error") if _("msg.connection_error") != "msg.connection_error" else "Cannot reach server. Check your internet connection.")
                return
            response_text = keys_text
            
            # Parse CSV - try multiple methods to handle various formats
            valid_keys = []
            
            # Method 1: Try CSV reader (handles quoted values)
            try:
                csv_reader = csv.reader(io.StringIO(response_text), quoting=csv.QUOTE_MINIMAL)
                for row in csv_reader:
                    for key in row:
                        key = key.strip()
                        # Normalize key: remove spaces (consistent with input normalization)
                        key_normalized = key.replace(' ', '')
                        if key_normalized:
                            valid_keys.append(key_normalized)
            except Exception as e:
                log_error(f"CSV reader failed: {e}")
            
            # Method 2: Also try simple line-by-line parsing (in case CSV format is different)
            if not valid_keys:
                for line in response_text.splitlines():
                    line = line.strip()
                    if line:
                        # Remove CSV quotes if present
                        if line.startswith('"') and line.endswith('"'):
                            line = line[1:-1]
                        # Handle escaped quotes
                        line = line.replace('""', '"')
                        # Normalize: remove spaces
                        key_normalized = line.replace(' ', '')
                        if key_normalized:
                            valid_keys.append(key_normalized)
            
            # Remove any spaces from input key (in case user accidentally added spaces when pasting)
            normalized_input = _key.strip().replace(' ', '')
            
            # Debug logging
            _logging.debug(f"Looking for key: {normalized_input}")
            _logging.debug(f"Found {len(valid_keys)} keys in CSV")
            if len(valid_keys) <= 10:  # Only log if reasonable number
                _logging.debug(f"Valid keys: {valid_keys}")

            # Try exact match first
            if normalized_input not in valid_keys:
                # Try case-insensitive match (in case there's a case mismatch)
                normalized_lower = normalized_input.lower()
                matched_key = None
                for key in valid_keys:
                    if key.lower() == normalized_lower:
                        matched_key = key
                        break
                
                if matched_key:
                    # Use the matched key (preserve original case from CSV)
                    normalized_input = matched_key
                else:
                    if hasattr(self, '_activation_error_label'):
                        self._activation_error_label.config(text=_("activation.invalid_key"))
                    return

            # Remove the key from keys.csv (use normalized key)
            valid_keys.remove(normalized_input)
            self._update_keys_csv(valid_keys)

            _hwid = self._generate_hwid()
            self._append_hwid(_hwid)
            self._save_verified_hwid(_hwid)

            # Send notification
            self._send_discord_notification(_key)
            
            # Show loading animation and wait for GitHub processing
            self._show_loading_animation(120)  # 2 minutes (120 seconds)

        except Exception as e:
            log_error(e)
            error_msg = f"Failed to validate key. Error: {str(e)}"
            if hasattr(self, '_activation_error_label'):
                self._activation_error_label.config(text=error_msg)
            else:
                _messagebox.showerror(_("msg.error"), error_msg)
    
    def _unlock_application(self):
        """Hide activation overlay and show the main application."""
        if not self._is_root_alive():
            return

        # Show terms BEFORE showing main content to prevent both windows being visible
        self._show_terms()

        # Hide activation overlay
        self._activation_overlay.grid_remove()

        # Show the notebook (main application)
        self.notebook.grid()

        # Create settings icon button integrated into notebook

        # Create widgets
        self._create_widgets()
        # Copy MUSIC_CREDITS.txt to .autobe folder so user has the YouTube credit link (non-blocking, safe)
        try:
            self._ensure_music_credits_file()
        except Exception:
            pass
        # Start background music once main screen is ready; try soon and retry if mixer not ready
        def _start_music_then_retry_if_silent():
            self._start_background_music()
            def _retry_if_not_playing(delay_next=2500):
                if not getattr(self, "_root", None) or not self._root.winfo_exists():
                    return
                if not getattr(self, "background_music_var", None) or not self.background_music_var.get():
                    return
                try:
                    if _PYGAME_MIXER_AVAILABLE and _pygame and _pygame.mixer.get_init() and not _pygame.mixer.music.get_busy():
                        self._start_background_music()
                    if delay_next and delay_next <= 6000:
                        self._root.after(delay_next, lambda dn=delay_next + 2500: _retry_if_not_playing(dn))
                except Exception:
                    pass
            self._root.after(2500, lambda: _retry_if_not_playing(2500))
        self._root.after(400, _start_music_then_retry_if_silent)
        self._root.after(900, _start_music_then_retry_if_silent)
        
        # Update Discord presence
        self._update_discord_presence(tab_name="AutoBE")
        
        # Auto-check for new release after delay (only prompts if update exists; delay avoids popup while opening Settings)
        self._root.after(6000, self._auto_check_for_updates)
        # Re-check periodically so the app always knows about new releases (silent when up to date)
        self._root.after(UPDATE_CHECK_INTERVAL_MS, self._periodic_update_check)
        # Show update outcome notice after UI has stabilized.
        self._root.after(1200, self._show_post_update_result_notice)
        # Keep Windows "Installed apps" version in sync after in-app exe updates.
        self._root.after(1500, self._sync_windows_uninstall_metadata)
        
        _logging.debug('Application unlocked.')

    def _show_post_update_result_notice(self):
        """If updater provided a result marker, show a one-time status dialog."""
        try:
            result = (getattr(self, "_pending_update_result", None) or "").strip().lower()
            if not result:
                return
            self._pending_update_result = None
            if result == "updated_ok":
                self._show_themed_info_dialog(
                    _("update.title"),
                    "Update completed successfully.\nYou are now running the new version.",
                    topmost=True,
                )
            elif result == "updated_rollback":
                self._show_themed_info_dialog(
                    _("update.failed"),
                    "Update could not start correctly, so AutoBE automatically rolled back to the previous version.",
                    topmost=True,
                )
            elif result == "updated_copy_failed":
                self._show_themed_info_dialog(
                    _("update.failed"),
                    "Update installation failed while replacing files.\nAutoBE kept your previous installed version.",
                    topmost=True,
                )
        except Exception:
            pass

    def _sync_windows_uninstall_metadata(self):
        """Sync uninstall DisplayName/DisplayVersion so Windows Apps list reflects current APP_VERSION."""
        if platform.system() != "Windows" or _winreg is None:
            return
        targets = [
            (_winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Uninstall"),
            (_winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Uninstall"),
            (_winreg.HKEY_LOCAL_MACHINE, r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
        ]
        desired_name = f"AutoBE version {APP_VERSION}"
        for root, base_path in targets:
            try:
                with _winreg.OpenKey(root, base_path, 0, _winreg.KEY_READ | _winreg.KEY_WRITE) as base:
                    i = 0
                    while True:
                        try:
                            subkey_name = _winreg.EnumKey(base, i)
                            i += 1
                        except OSError:
                            break
                        try:
                            with _winreg.OpenKey(base, subkey_name, 0, _winreg.KEY_READ | _winreg.KEY_WRITE) as sub:
                                try:
                                    display_name, _ = _winreg.QueryValueEx(sub, "DisplayName")
                                except Exception:
                                    continue
                                dn = str(display_name or "").lower()
                                if "autobe" not in dn:
                                    continue
                                try:
                                    _winreg.SetValueEx(sub, "DisplayVersion", 0, _winreg.REG_SZ, APP_VERSION)
                                except Exception:
                                    pass
                                # Keep naming style consistent with installer default style.
                                try:
                                    _winreg.SetValueEx(sub, "DisplayName", 0, _winreg.REG_SZ, desired_name)
                                except Exception:
                                    pass
                        except Exception:
                            continue
            except Exception:
                continue
    
    def _update_keys_csv(self, valid_keys):
        """Update the keys.csv file by removing the used key"""
        _keys_file_url = "https://api.github.com/repos/FrostyHostMC/AutoBE/contents/keys.csv"
        _headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Content-Type": "application/json"
        }
        # Recreate the keys.csv content using proper CSV formatting
        output = io.StringIO()
        csv_writer = csv.writer(output)
        # Write each key as a separate row (properly handles special characters)
        for key in valid_keys:
            csv_writer.writerow([key])
        new_content = output.getvalue().encode('utf-8')
        
        # Base64 encode the content
        encoded_content = base64.b64encode(new_content).decode('utf-8')
        
        try:
            # Get the SHA of the current file
            response = _requests.get(_keys_file_url, headers=_headers)
            response.raise_for_status()
            sha = response.json()['sha']

            # Update the file on GitHub with the new content
            update_data = {
                "message": "Remove used activation key",
                "content": encoded_content,
                "sha": sha
            }
            response = _requests.put(_keys_file_url, json=update_data, headers=_headers)
            response.raise_for_status()
        except Exception as e:
            log_error(e)
            raise Exception(f"Failed to update keys.csv: {str(e)}")

    def _append_to_blacklist(self, _hwid):
        """Append HWID to the blacklist on GitHub"""
        blacklist_file_url = "https://api.github.com/repos/FrostyHostMC/AutoBE/contents/blacklist.txt"
        _headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Content-Type": "application/json"
        }
        try:
            response = _requests.get(blacklist_file_url, headers=_headers)
            response.raise_for_status()
            
            file_data = response.json()
            current_content = base64.b64decode(file_data['content']).decode('utf-8').rstrip()
            sha = file_data['sha']

            # Check if HWID already in blacklist
            if _hwid in current_content:
                return  # Already banned
            
            updated_content = f"{current_content}\n{_hwid}\n" if current_content else f"{_hwid}\n"
            encoded_content = base64.b64encode(updated_content.encode('utf-8')).decode('utf-8')
            
            update_data = {
                "message": "Auto-ban spoofer",
                "content": encoded_content,
                "sha": sha
            }
            put_response = _requests.put(blacklist_file_url, json=update_data, headers=_headers)
            put_response.raise_for_status()
            
            return put_response.json()

        except _requests.exceptions.RequestException as req_err:
            log_error(f"Failed to append to blacklist: {req_err}")
            raise
    
    def _detect_spoofing(self, _hwid):
        """Detect hardware spoofing / VM using multiple checks on Windows, Linux, and macOS. Returns True if detected."""
        spoofing_flags = []
        try:
            # Computer name / hostname (all platforms) - VM patterns
            try:
                computer_name = platform.node().lower()
                vm_patterns = ["vmware", "virtualbox", "vbox", "qemu", "xen", "kvm", "parallels", "bochs", "innotek", "hyper-v", "hyperv"]
                if any(pattern in computer_name for pattern in vm_patterns):
                    spoofing_flags.append("vm_computer_name")
            except Exception:
                pass
            
            if platform.system() == "Windows":
                # --- Windows: WMIC / getmac checks ---
                try:
                    output = subprocess.check_output(
                        ["wmic", "baseboard", "get", "serialnumber"],
                        stderr=subprocess.STDOUT,
                        text=True,
                        timeout=5
                    ).splitlines()
                    serial = next(
                        (line.strip().lower() for line in output if line.strip() and "serialnumber" not in line.lower()),
                        ""
                    )
                    generic_serials = ["to be filled by o.e.m.", "", "default string", "oem", "default", "system serial number"]
                    if serial in generic_serials:
                        spoofing_flags.append("generic_motherboard_serial")
                except Exception:
                    pass
                try:
                    output = subprocess.check_output(
                        ["wmic", "cpu", "get", "processorid"],
                        stderr=subprocess.STDOUT,
                        text=True,
                        timeout=5
                    ).splitlines()
                    cpu_id = next(
                        (line.strip().lower() for line in output if line.strip() and "processorid" not in line.lower()),
                        ""
                    )
                    if not cpu_id or cpu_id == "0000000000000000" or len(cpu_id) < 8:
                        spoofing_flags.append("invalid_cpu_id")
                except Exception:
                    pass
                try:
                    output = subprocess.check_output(
                        ["wmic", "diskdrive", "get", "serialnumber"],
                        stderr=subprocess.STDOUT,
                        text=True,
                        timeout=5
                    ).splitlines()
                    disk_serials = [line.strip().lower() for line in output if line.strip() and "serialnumber" not in line.lower()]
                    # Only flag when ALL disks have generic serials (one USB/secondary drive with no serial is common on real PCs)
                    if disk_serials and all(s in ["", "none", "00000000"] for s in disk_serials):
                        spoofing_flags.append("generic_disk_serial")
                except Exception:
                    pass
                # Check system manufacturer/model for VM *before* getmac so we can avoid false positives from Hyper-V/Docker/WSL2 virtual NICs on real PCs
                # Note: "microsoft corporation" and "oracle" omitted — real Surface/OEM and Oracle servers report these
                try:
                    out = subprocess.check_output(
                        ["wmic", "computersystem", "get", "manufacturer,model"],
                        stderr=subprocess.STDOUT,
                        text=True,
                        timeout=5
                    ).lower()
                    vm_manufacturer = ["vmware", "virtualbox", "vbox", "qemu", "xen", "innotek", "parallels", "bochs"]
                    if any(m in out for m in vm_manufacturer):
                        spoofing_flags.append("vm_system_manufacturer")
                except Exception:
                    pass
                try:
                    output = subprocess.check_output(
                        ["getmac", "/fo", "csv", "/nh"],
                        stderr=subprocess.STDOUT,
                        text=True,
                        timeout=5
                    )
                    # Only flag VM MAC if we already have a VM indicator (manufacturer or computer name).
                    # Real PCs often have Hyper-V/Docker/WSL2 virtual adapters with VM MACs — avoid false bans.
                    # Also exclude VPN adapters (NordVPN, ExpressVPN, etc. use virtual NICs with similar MAC ranges)
                    vm_mac_prefixes = ["00-05-69", "00-0c-29", "00-50-56", "08-00-27", "00-15-5d", "00:05:69", "00:0c:29", "00:50:56", "08:00:27", "00:15:5d"]
                    # VPN adapter names to exclude (case-insensitive)
                    vpn_adapter_names = ["nordvpn", "expressvpn", "surfshark", "cyberghost", "private internet access", "pia", "protonvpn", "windscribe", "tunnelbear", "hotspot shield", "vpn"]
                    output_lower = output.lower()
                    has_vm_mac = any(prefix.lower() in output_lower for prefix in vm_mac_prefixes)
                    has_vpn_adapter = any(vpn_name in output_lower for vpn_name in vpn_adapter_names)
                    if has_vm_mac and not has_vpn_adapter:
                        if "vm_system_manufacturer" in spoofing_flags or "vm_computer_name" in spoofing_flags:
                            spoofing_flags.append("vm_mac_address")
                except Exception:
                    pass
                try:
                    output = subprocess.check_output(
                        ["wmic", "bios", "get", "version"],
                        stderr=subprocess.STDOUT,
                        text=True,
                        timeout=5
                    ).splitlines()
                    bios_version = next(
                        (line.strip().lower() for line in output if line.strip() and "version" not in line.lower()),
                        ""
                    )
                    # "bios" alone is too generic — many real BIOSes report it; only flag clearly placeholder values
                    if bios_version in ["default", "system bios", ""]:
                        spoofing_flags.append("generic_bios")
                except Exception:
                    pass
                # --- Windows: VM video controller (VMware SVGA, VirtualBox Graphics, VirtIO, etc.) ---
                try:
                    output = subprocess.check_output(
                        ["wmic", "path", "win32_videocontroller", "get", "name"],
                        stderr=subprocess.STDOUT,
                        text=True,
                        timeout=5
                    ).lower()
                    vm_video_keywords = ["vmware", "virtualbox", "vbox", "qemu", "parallels", "virtio", "red hat virtio", "vmware svga", "virtualbox graphics", "bochs"]
                    if any(kw in output for kw in vm_video_keywords):
                        spoofing_flags.append("vm_video_controller")
                except Exception:
                    pass
                # --- Windows: HypervisorPresent (guest often reports True; host with Hyper-V can too, so just one extra signal) ---
                try:
                    output = subprocess.check_output(
                        ["wmic", "computersystem", "get", "hypervisorpresent"],
                        stderr=subprocess.STDOUT,
                        text=True,
                        timeout=5
                    ).lower()
                    if "true" in output and ("vm_system_manufacturer" in spoofing_flags or "vm_computer_name" in spoofing_flags or "vm_video_controller" in spoofing_flags):
                        spoofing_flags.append("win_hypervisor_present")
                except Exception:
                    pass
            
            elif platform.system() == "Linux":
                # --- Linux: containers (Docker/Podman etc.) = not real hardware ---
                try:
                    if _os.path.isfile("/.dockerenv") or _os.path.isfile("/run/.containerenv"):
                        spoofing_flags.append("linux_container")
                except Exception:
                    pass
                # --- Linux: hypervisor, DMI, and VM MAC checks ---
                try:
                    with open("/proc/cpuinfo", "r", encoding="utf-8", errors="ignore") as f:
                        cpuinfo = f.read().lower()
                    if "hypervisor" in cpuinfo:
                        spoofing_flags.append("linux_hypervisor")
                except Exception:
                    pass
                # DMI/sysfs: product name, sys_vendor, board_vendor often expose VM/cloud
                vm_dmi_keywords = [
                    "vmware", "virtualbox", "vbox", "qemu", "xen", "kvm", "innotek", "bochs",
                    "amazon ec2", "parallels", "openstack", "innotek gmbh",
                    "google compute engine", "digitalocean", "linode", "vultr", "oracle vm",
                    "red hat openstack", "rhev", "kvm/rhel", "openstack foundation"
                ]
                try:
                    dmi_base = "/sys/class/dmi/id"
                    for name in ["product_name", "sys_vendor", "board_vendor", "bios_vendor", "product_family"]:
                        path = _os.path.join(dmi_base, name)
                        if _os.path.isfile(path):
                            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                                val = f.read().strip().lower()
                            if any(kw in val for kw in vm_dmi_keywords):
                                spoofing_flags.append("linux_vm_dmi")
                                break
                except Exception:
                    pass
                # MAC addresses: virtual NIC prefixes (VMware, VirtualBox, QEMU/KVM, Hyper-V, Parallels)
                vm_mac_prefixes_linux = [
                    "00:05:69", "00:0c:29", "00:50:56", "08:00:27", "00:15:5d", "52:54:00",
                    "0a:00:27", "02:00:00", "00:1c:42", "00:03:ff", "00:0d:3a", "00:22:aa"
                ]
                try:
                    net_path = "/sys/class/net"
                    if _os.path.isdir(net_path):
                        for iface in _os.listdir(net_path):
                            if iface in ("lo", "bonding_masters"):
                                continue
                            addr_path = _os.path.join(net_path, iface, "address")
                            if _os.path.isfile(addr_path):
                                with open(addr_path, "r", encoding="utf-8", errors="ignore") as f:
                                    mac = f.read().strip().lower().replace("-", ":")
                                if any(mac.startswith(p.replace("-", ":")) for p in vm_mac_prefixes_linux):
                                    spoofing_flags.append("linux_vm_mac")
                                    break
                except Exception:
                    pass
                # --- Linux: systemd-detect-virt (reliable VM/container detection when available) ---
                try:
                    out = subprocess.check_output(
                        ["systemd-detect-virt"],
                        stderr=subprocess.DEVNULL,
                        text=True,
                        timeout=3
                    ).strip().lower()
                    # "none" = bare metal; "container" already covered by .dockerenv/.containerenv; anything else is VM or container
                    if out and out != "none":
                        spoofing_flags.append("linux_systemd_virt")
                except (FileNotFoundError, subprocess.CalledProcessError, OSError):
                    pass
                except Exception:
                    pass
                # --- Linux: virtio devices (strong VM indicator; rare on real hardware) ---
                try:
                    virtio_path = "/sys/bus/virtio/devices"
                    if _os.path.isdir(virtio_path) and len(_os.listdir(virtio_path)) > 0:
                        spoofing_flags.append("linux_virtio_devices")
                except Exception:
                    pass
            
            elif platform.system() == "Darwin":
                # --- macOS: VM detection via system_profiler or model identifier ---
                try:
                    out = subprocess.check_output(
                        ["system_profiler", "SPHardwareDataType"],
                        stderr=subprocess.DEVNULL,
                        text=True,
                        timeout=10
                    ).lower()
                    if "vmware" in out or "parallels" in out or "virtualbox" in out or "vbox" in out:
                        spoofing_flags.append("macos_vm")
                except Exception:
                    pass
                try:
                    # Model identifier often contains VM name on macOS VMs
                    out = subprocess.check_output(
                        ["sysctl", "-n", "hw.model"],
                        stderr=subprocess.DEVNULL,
                        text=True,
                        timeout=5
                    ).lower()
                    if "vmware" in out or "parallels" in out or "virtualbox" in out or "vbox" in out:
                        spoofing_flags.append("macos_vm")
                except Exception:
                    pass
                # --- macOS: ioreg can expose VM vendor strings even when system_profiler is spoofed ---
                try:
                    out = subprocess.check_output(
                        ["ioreg", "-l"],
                        stderr=subprocess.DEVNULL,
                        text=True,
                        timeout=5
                    ).lower()
                    if "vmware" in out or "parallels" in out or "virtualbox" in out or "innotek" in out or "vbox" in out:
                        spoofing_flags.append("macos_ioreg_vm")
                except Exception:
                    pass
            
            # Block only when we have strong evidence: require at least 5 indicators AND at least 1 VM-specific indicator
            # to avoid false positives (many real PCs have generic OEM serials, Hyper-V/Docker NICs, etc.)
            # VM-specific indicators: vm_computer_name, vm_system_manufacturer, vm_video_controller, vm_mac_address,
            # linux_container, linux_hypervisor, linux_vm_dmi, linux_vm_mac, linux_systemd_virt, linux_virtio_devices,
            # macos_vm, macos_ioreg_vm
            vm_specific_flags = [f for f in spoofing_flags if f.startswith(('vm_', 'linux_', 'macos_'))]
            if len(spoofing_flags) >= 5 and len(vm_specific_flags) >= 1:
                log_message = f"Spoofing/VM detected - Flags: {', '.join(spoofing_flags)}, HWID: {_hwid}"
                _logging.warning(log_message)
                log_error(log_message)
                return True
            
        except Exception as e:
            log_error(f"Spoofing detection error: {e}")
            return False
        
        return False
    
    def _append_hwid(self, _hwid):
        """Append HWID to the whitelist on GitHub"""
        _hwid_file_url = "https://api.github.com/repos/FrostyHostMC/AutoBE/contents/hwid_address.txt"
        _headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Content-Type": "application/json"
        }
        try:
            response = _requests.get(_hwid_file_url, headers=_headers)
            response.raise_for_status()
            
            file_data = response.json()
            current_content = base64.b64decode(file_data['content']).decode('utf-8').rstrip()
            sha = file_data['sha']

            updated_content = f"{current_content}\n{_hwid}\n"
            encoded_content = base64.b64encode(updated_content.encode('utf-8')).decode('utf-8')
            
            update_data = {
                "message": "Add new HWID",
                "content": encoded_content,
                "sha": sha
            }
            put_response = _requests.put(_hwid_file_url, json=update_data, headers=_headers)
            put_response.raise_for_status()
            
            return put_response.json()

        except _requests.exceptions.RequestException as req_err:
            log_error(req_err)
            raise Exception(f"HTTP request failed: {str(req_err)}")
        except Exception as e:
            log_error(e)
            raise Exception(f"Failed to update hwid_address.txt: {str(e)}")

    def _send_discord_notification(self, _key):
        """Send activation notification to Discord"""
        _hwid = self._generate_hwid()
        _webhook_url = "https://discord.com/api/webhooks/1279960853969502248/Y7VR7m6qEEe0UScvkZLe1IJO4lK-p7AP8_RAoXsWbsbrBui_geLnA_DW1TFJvvEA-ptg"
        _data = {
            "content": f"Activation key used: {_key}\nHWID: {_hwid}"
        }
        _requests.post(_webhook_url, json=_data)
        
    def _show_terms(self):
        # Main window is already hidden from __init__
        # Create terms window
        self._terms_window = _T1(self._root)
        self._root.wait_window(self._terms_window._w1)
        _logging.debug('Terms of Use window closed.')
        # Show main window after terms are accepted with smooth transition
        self._root.deiconify()
        self._root.lift()
        self._root.focus_force()
        self._root.update_idletasks()
        # Apply taskbar button fix after showing main window
        # Single attempt with minimal delay to reduce flickering
        self._root.after(150, lambda: _force_taskbar_button(self._root))
        self._root.after(300, lambda: self._apply_window_icon(self._root))

    def _create_widgets(self):
        # Create widgets inside the App1 Tab (app1_frame) - Modern styling
        # Configure app1_frame for proper resizing
        self.app1_frame.grid_columnconfigure(0, weight=1)
        self.app1_frame.grid_rowconfigure(0, weight=1, minsize=340)  # Files frame - expandable
        self.app1_frame.grid_rowconfigure(1, weight=0)  # Output frame - fixed
        self.app1_frame.grid_rowconfigure(2, weight=0)  # Buttons frame - fixed
        self.app1_frame.grid_rowconfigure(3, weight=0)  # Progress frame - fixed (don't shrink)
        
        self._frame_files = _tk.LabelFrame(self.app1_frame, text="📦 " + _("app.select_mcpacks"), bg='#1a1a1a', fg='#FFFFFF', font=("Segoe UI", 13, "bold"))
        self._frame_files.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")

        # File list: (display_name, path, photo_or_none) per item; photo refs kept to avoid GC
        self._file_list_data = []
        self._file_list_photo_refs = []
        self._file_list_selected = set()
        self._file_paths = {}
        self._files = []

        listbox_frame = _tk.Frame(self._frame_files, bg='#1a1a1a')
        listbox_frame.grid(row=0, column=0, padx=12, pady=(12, 8), sticky="nsew")
        listbox_frame.grid_columnconfigure(0, weight=1)
        listbox_frame.grid_rowconfigure(0, weight=1)
        self._file_list_canvas = _tk.Canvas(listbox_frame, bg='#0A0A0A', highlightthickness=0, yscrollincrement=40)
        self._file_list_canvas.grid(row=0, column=0, sticky="nsew")
        self._file_list_inner = _tk.Frame(self._file_list_canvas, bg='#0A0A0A')
        self._file_list_canvas_window = self._file_list_canvas.create_window(0, 0, window=self._file_list_inner, anchor='nw')
        def _on_file_list_configure(event):
            self._file_list_canvas.configure(scrollregion=self._file_list_canvas.bbox('all'))
            self._file_list_canvas.itemconfig(self._file_list_canvas_window, width=event.width)
        self._file_list_inner.bind('<Configure>', _on_file_list_configure)
        self._file_list_canvas.bind('<Configure>', lambda e: self._file_list_canvas.itemconfig(self._file_list_canvas_window, width=e.width))
        def _file_list_wheel(event):
            if getattr(event, 'num', None) == 4:
                self._file_list_canvas.yview_scroll(-3, 'units')
            elif getattr(event, 'num', None) == 5:
                self._file_list_canvas.yview_scroll(3, 'units')
            else:
                delta = getattr(event, 'delta', 0)
                units = max(1, abs(delta) // 40) * (-1 if delta > 0 else 1)
                self._file_list_canvas.yview_scroll(units, 'units')
        # Store so _rebuild_autobe_file_list can propagate to every row/label
        self._file_list_wheel_handler = _file_list_wheel
        for _ev in ('<MouseWheel>', '<Button-4>', '<Button-5>'):
            self._file_list_canvas.bind(_ev, _file_list_wheel)
            self._file_list_inner.bind(_ev, _file_list_wheel)

        # File count label + Select All button row
        _count_row = _tk.Frame(self._frame_files, bg='#1a1a1a')
        _count_row.grid(row=1, column=0, padx=12, pady=(0, 4), sticky="ew")
        _count_row.grid_columnconfigure(0, weight=1)
        self._file_count_label = _tk.Label(_count_row, text=_f("app.files_selected", n=0), bg='#1a1a1a', fg='#FFFFFF', font=("Segoe UI", 10))
        self._file_count_label.grid(row=0, column=0, sticky="w")
        self._btn_select_all = _tk.Button(_count_row, text="Select All", command=self._toggle_select_all_files,
            bg='#2d2d2d', fg='#CCCCCC', font=("Segoe UI", 9), relief='flat', cursor='hand2',
            activebackground='#3d3d3d', activeforeground='#FFFFFF', padx=10, pady=2)
        self._btn_select_all.grid(row=0, column=1, sticky="e")
        self._btn_select_all.grid_remove()  # hidden until files are added

        self._btn_add = _tk.Button(self._frame_files, text="➕ " + _("app.add_files"), command=self._add_files, bg='#9333ea', fg='#FFFFFF', font=("Segoe UI", 11, "bold"), relief='flat', cursor='hand2', activebackground='#a855f7')
        self._btn_add.grid(row=2, column=0, padx=12, pady=(0, 8), sticky="ew")

        self._btn_remove = _tk.Button(self._frame_files, text="🗑️ " + _("app.remove_selected"), command=self._remove_files, bg='#1a1a1a', fg='#FFFFFF', font=("Segoe UI", 11), relief='flat', cursor='hand2', activebackground='#2d2d2d')
        self._btn_remove.grid(row=3, column=0, padx=12, pady=(0, 12), sticky="ew")

        # Configure resizing for file frame
        self._frame_files.grid_columnconfigure(0, weight=1)
        self._frame_files.grid_rowconfigure(0, weight=1)  # Listbox frame - expandable
        self._frame_files.grid_rowconfigure(1, weight=0)  # File count row - fixed
        self._frame_files.grid_rowconfigure(2, weight=0)  # Add button - fixed
        self._frame_files.grid_rowconfigure(3, weight=0)  # Remove button - fixed

        self._frame_output = _tk.LabelFrame(self.app1_frame, text="📂 " + _("app.select_output_dir"), bg='#1a1a1a', fg='#FFFFFF', font=("Segoe UI", 13, "bold"))
        self._frame_output.grid(row=1, column=0, padx=15, pady=15, sticky="nsew")

        self._output_dir_var = _tk.StringVar()
        self._entry_output_dir = _tk.Entry(self._frame_output, textvariable=self._output_dir_var, width=50, bg='#0A0A0A', fg='#FFFFFF', font=("Segoe UI", 11), insertbackground='#a855f7', relief='flat', highlightthickness=1, highlightbackground='#1a1a1a', highlightcolor='#9333ea')
        self._entry_output_dir.grid(row=0, column=0, padx=12, pady=12, sticky="ew", ipady=8)

        self._btn_select_output = _tk.Button(self._frame_output, text=_("app.browse"), command=self._select_output_dir, bg='#9333ea', fg='#FFFFFF', font=("Segoe UI", 11, "bold"), relief='flat', cursor='hand2', activebackground='#a855f7')
        self._btn_select_output.grid(row=0, column=1, padx=(0, 12), pady=12, sticky="ew")

        # Configure resizing for output frame
        self._frame_output.grid_columnconfigure(0, weight=1)

        # Auto-Import vars kept as self attributes so the merge code can read them
        _ai_s = self._load_settings()
        self._auto_import_var = _tk.BooleanVar(value=_ai_s.get("auto_import", False))
        self._mc_path_var = _tk.StringVar(value=_ai_s.get("mc_path", "") or self._detect_com_mojang())
        self._auto_import_var.trace_add('write', lambda *a: self._save_settings())
        self._mc_path_var.trace_add('write', lambda *a: self._save_settings())

        self._frame_buttons = _tk.Frame(self.app1_frame, bg='#000000')
        self._frame_buttons.grid(row=2, column=0, padx=15, pady=15, sticky="ew")

        self._btn_start = _tk.Button(self._frame_buttons, text="🚀 " + _("app.start_process"), command=self._process_and_create_manifest, bg='#9333ea', fg='#FFFFFF', font=("Segoe UI", 12, "bold"), relief='flat', cursor='hand2', activebackground='#a855f7', padx=20, pady=10)
        self._btn_start.grid(row=0, column=0, padx=(0, 8), pady=0, sticky="ew")

        self._btn_check = _tk.Button(self._frame_buttons, text="🔍 " + _("app.check_packs"), command=self._extract_and_show_codes, bg='#9333ea', fg='#FFFFFF', font=("Segoe UI", 12, "bold"), relief='flat', cursor='hand2', activebackground='#a855f7', padx=20, pady=10)
        self._btn_check.grid(row=0, column=1, padx=(8, 4), pady=0, sticky="ew")

        # Excel organization button
        self._btn_excel = _tk.Button(self._frame_buttons, text="📊 Excel", command=self._show_excel_manager, bg='#10b981', fg='#FFFFFF', font=("Segoe UI", 12, "bold"), relief='flat', cursor='hand2', activebackground='#059669', padx=20, pady=10)
        self._btn_excel.grid(row=0, column=2, padx=(4, 4), pady=0, sticky="ew")

        # Achievement Status Button (click opens in-app achievement screen)
        self._btn_achievement_status = _tk.Button(self._frame_buttons, text="✅ " + _("app.achievements_active"), command=self._show_achievement_overlay, bg='#10b981', fg='#FFFFFF', font=("Segoe UI", 11, "bold"), relief='flat', cursor='hand2', activebackground='#059669', padx=15, pady=10)
        self._btn_achievement_status.grid(row=0, column=3, padx=(4, 0), pady=0, sticky="ew")
        
        # Store achievement-disabling packs for overlay screen
        self._achievement_disabling_packs = []
        
        # Initialize achievement status
        self._check_achievement_compatibility()

        # Configure resizing for buttons frame
        self._frame_buttons.grid_columnconfigure(0, weight=1)
        self._frame_buttons.grid_columnconfigure(1, weight=1)
        self._frame_buttons.grid_columnconfigure(2, weight=1)
        self._frame_buttons.grid_columnconfigure(3, weight=0)  # Achievement button - fixed width

        # Progress Display Section - Game-style loading screen
        self._frame_progress = _tk.LabelFrame(self.app1_frame, text="📊 " + _("app.processing_progress"), bg='#1a1a1a', fg='#FFFFFF', font=("Segoe UI", 13, "bold"))
        self._frame_progress.grid(row=3, column=0, padx=15, pady=15, sticky="nsew")
        self._frame_progress.columnconfigure(0, weight=1)
        self._frame_progress.grid_rowconfigure(0, weight=0)  # Progress container - fixed height
        
        progress_container = _tk.Frame(self._frame_progress, bg='#1a1a1a')
        progress_container.grid(row=0, column=0, padx=12, pady=12, sticky="nsew")
        progress_container.columnconfigure(0, weight=1)
        progress_container.rowconfigure(0, weight=0)  # Step label - fixed
        progress_container.rowconfigure(1, weight=0)  # Progress bar - fixed
        progress_container.rowconfigure(2, weight=0)  # Steps frame - fixed
        
        # Current step label
        self._progress_step_label = _tk.Label(progress_container, text=_("app.ready_to_process"), 
                                             bg='#1a1a1a', fg='#FFFFFF', 
                                             font=('Segoe UI', 12, 'bold'),
                                             anchor='w')
        self._progress_step_label.grid(row=0, column=0, sticky="w", pady=(0, 8))
        
        # Progress bar
        style = _ttk.Style()
        style.theme_use('clam')
        style.configure("Progress.Horizontal.TProgressbar", background='#9333ea', troughcolor='#0A0A0A', borderwidth=0)
        self._progress = _ttk.Progressbar(progress_container, orient='horizontal', 
                                         length=400, mode='determinate', 
                                         style="Progress.Horizontal.TProgressbar",
                                         maximum=100)
        self._progress.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        
        # Steps indicator (4 steps)
        steps_frame = _tk.Frame(progress_container, bg='#1a1a1a')
        steps_frame.grid(row=2, column=0, sticky="ew")
        
        self._step_labels = []
        step_names = [_("progress.creating_manifest"), _("progress.processing_files"), _("progress.updating_packs"), _("progress.finalizing")]
        for i, step_name in enumerate(step_names):
            step_frame = _tk.Frame(steps_frame, bg='#1a1a1a')
            step_frame.grid(row=0, column=i, padx=5, sticky="w")
            
            # Step number/status indicator
            step_status = _tk.Label(step_frame, text="○", bg='#1a1a1a', fg='#666666',
                                   font=('Segoe UI', 14), width=3, anchor='w')
            step_status.pack(side='left')
            self._step_labels.append({'status': step_status, 'name': step_name})
            
            # Step name
            step_label = _tk.Label(step_frame, text=step_name, bg='#1a1a1a', fg='#999999',
                                  font=('Segoe UI', 9))
            step_label.pack(side='left')
            self._step_labels[i]['label'] = step_label
        
        self._trademark_label = _tk.Label(self.app1_frame, text=_("app.codenex"), bg='#000000', fg='#FFFFFF', font=("Segoe UI", 10))
        self._trademark_label.grid(row=4, column=0, padx=15, pady=10, sticky="e")
        
        # Update app1_frame row configuration
        self.app1_frame.grid_rowconfigure(4, weight=0)  # Trademark - fixed
