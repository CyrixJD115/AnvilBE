"""
MergeWorkerThread — runs the complete merge pipeline in a background thread
and communicates progress via Qt signals.
"""
import json
import logging
import os
import re
import shutil
import traceback
import zipfile
from PySide6.QtCore import QThread, Signal
from src.core.i18n import _tr
from src.core.pack_utils import safe_extractall, zip_pack_folder


class MergeWorkerThread(QThread):
    """
    Worker thread for background pack merging operations.
    Emits progress/status/finished/error signals to update the GUI.
    Checks self._cancel_requested between steps and exits cleanly if set.
    """

    progress_update = Signal(int)
    status_update = Signal(str)
    finished = Signal(bool, str)
    error = Signal(str)

    def __init__(self, app_instance, files, output_dir):
        super().__init__()
        self.app = app_instance
        self.files = files
        self.output_dir = output_dir
        self._cancel_requested = False
        self.setObjectName("MergeWorkerThread")

    def cancel(self):
        """Request cancellation of the merge process."""
        self._cancel_requested = True

    def _check_cancelled(self):
        """Return True if cancel was requested (for inline checks)."""
        return self._cancel_requested

    def run(self):
        """
        Execute the complete merge process in the background.
        When merge_by_version is enabled, each version group is processed
        through the full pipeline (steps 4-16) independently so that
        manifests, scripts, textures, and packaging all run per group.
        """
        try:
            if not self._run_preprocessing():
                return

            if getattr(self.app, 'merge_by_version', False):
                self._run_merge_by_version()
            else:
                self._run_merge_pipeline(self.files, self.output_dir)

            if self._cancel_requested:
                self.finished.emit(False, _tr("status.cancelled", "Cancelled"))
                return

            self.progress_update.emit(100)
            self.status_update.emit(_tr("status.complete", "Complete!"))
            self.finished.emit(True, _tr("status.merged_success",
                                          "All packs merged successfully!"))

        except Exception as e:
            logging.error(f"Error during processing: {e}", exc_info=True)
            self.error.emit(str(e))
            self.finished.emit(False, f"An error occurred: {e}")

    # ── Steps 1-3: run once regardless of mode ──────────────────────

    def _run_preprocessing(self):
        """Run validation, version extraction, and compatibility check."""
        # Step 1: Validate files
        if self._cancel_requested:
            self.finished.emit(False, _tr("status.cancelled", "Cancelled"))
            return False
        self.progress_update.emit(5)
        self.status_update.emit(_tr("progress.validating", "Validating files..."))
        if not self.app._validate_files(show_gui=False):
            self.finished.emit(False, _tr("status.validation_failed", "Validation failed"))
            return False

        # Step 2: Extract and store highest versions
        if self._cancel_requested:
            self.finished.emit(False, _tr("status.cancelled", "Cancelled"))
            return False
        self.progress_update.emit(10)
        self.status_update.emit(_tr("progress.extracting_versions",
                                     "Extracting version information..."))
        self.app._extract_and_store_highest_versions()

        # Step 3: Check compatibility
        if self._cancel_requested:
            self.finished.emit(False, _tr("status.cancelled", "Cancelled"))
            return False
        self.progress_update.emit(15)
        self.status_update.emit(_tr("progress.checking_compat", "Checking compatibility..."))
        self.app._check_compatibility(show_gui=False)

        return True

    # ── Merge-by-version orchestration ───────────────────────────────

    def _run_merge_by_version(self):
        """Group files by version and run the full pipeline per group."""
        import uuid
        groups = self.app._group_files_by_version(self.files)
        original_out_dir = self.app._out_dir
        total = len(groups)

        # Pre-generate a single RP UUID so all BP groups can depend on it
        self.app._pre_generated_rp_uuid = str(uuid.uuid4())
        self.app._pre_generated_rp_module_uuid = str(uuid.uuid4())
        # Collect BP UUIDs as they're created
        self.app._all_bp_uuids = []

        for idx, (version, version_files) in enumerate(groups.items()):
            if self._cancel_requested:
                break

            safe_ver = version.replace(' ', '_').replace('.', '_')
            ver_out = os.path.join(self.output_dir, f"v{safe_ver}")
            os.makedirs(ver_out, exist_ok=True)
            self.app._out_dir = ver_out

            # Store this group's script API version for manifest dependencies
            if version.lower() not in ('unknown', 'none', ''):
                self.app._current_script_api_version = version
            else:
                self.app._current_script_api_version = None

            label = f"v{safe_ver}"
            self.status_update.emit(
                f"[{label}] Processing version group {idx + 1}/{total}..."
            )
            logging.info(f"=== Merge by version: group {idx + 1}/{total} "
                          f"({label}, {len(version_files)} packs) ===")

            self._run_merge_pipeline(version_files, ver_out)

        # Update the RP manifest to depend on ALL BP UUIDs
        self._link_rp_to_all_bps()

        # Restructure output into flat behavior_packs/ and resource_packs/
        self._restructure_version_output()

        # Clean up temporary UUID state
        for attr in ('_pre_generated_rp_uuid', '_pre_generated_rp_module_uuid',
                     '_all_bp_uuids', '_current_script_api_version'):
            if hasattr(self.app, attr):
                delattr(self.app, attr)

        self.app._out_dir = original_out_dir

    def _link_rp_to_all_bps(self):
        """After all groups are processed, update the RP manifest to include
        dependencies on every BP UUID so activating the RP auto-loads all BPs."""
        import zipfile
        import json
        import tempfile
        bp_uuids = getattr(self.app, '_all_bp_uuids', [])
        if not bp_uuids:
            return

        # Find the RP file across all version subdirectories
        for entry in sorted(os.listdir(self.output_dir)):
            ver_path = os.path.join(self.output_dir, entry)
            if not os.path.isdir(ver_path) or not entry.startswith('v'):
                continue

            fmt = getattr(self.app, '_output_format', 'mcpack')
            ext = '.zip' if fmt == 'zip' else '.mcpack'
            rp_file = os.path.join(ver_path, f'resource_pack{ext}')
            if not os.path.isfile(rp_file):
                continue

            tmp = tempfile.mkdtemp(prefix='rplink_')
            try:
                with zipfile.ZipFile(rp_file, 'r') as z:
                    safe_extractall(z, tmp)
                mpath = os.path.join(tmp, 'manifest.json')
                if os.path.isfile(mpath):
                    with open(mpath, 'r', encoding='utf-8') as f:
                        mdata = json.load(f)
                    deps = mdata.get('dependencies', [])
                    for bp_uuid in bp_uuids:
                        if not any(d.get('uuid') == bp_uuid for d in deps):
                            deps.append({"uuid": bp_uuid, "version": [1, 0, 0]})
                    mdata['dependencies'] = deps
                    with open(mpath, 'w', encoding='utf-8') as f:
                        json.dump(mdata, f, indent=2)
                    zip_pack_folder(tmp, rp_file)
                    logging.info(f"Updated RP manifest with {len(bp_uuids)} BP dependencies")
            except Exception as e:
                logging.warning(f"Failed to link RP to BPs: {e}")
            finally:
                try:
                    shutil.rmtree(tmp)
                except Exception:
                    pass

    def _restructure_version_output(self):
        """After merge-by-version, reorganize per-version subdirectories into
        two flat folders: behavior_packs/ and resource_packs/.

        Files are named: <PackName>_<version>_BP.<ext> (version omitted if
        the group has no script API dependency).
        Removes the v*/ subdirectories after extracting the final pack files.
        """
        out = self.output_dir
        bp_dir = os.path.join(out, 'behavior_packs')
        rp_dir = os.path.join(out, 'resource_packs')
        os.makedirs(bp_dir, exist_ok=True)
        os.makedirs(rp_dir, exist_ok=True)

        fmt = getattr(self.app, '_output_format', 'mcpack')
        ext = '.zip' if fmt == 'zip' else '.mcpack'

        def _read_pack_name(pack_path):
            """Read pack name from manifest.json inside a .mcpack/.zip."""
            try:
                with zipfile.ZipFile(pack_path, 'r') as z:
                    with z.open('manifest.json') as f:
                        manifest = json.load(f)
                        name = manifest.get('header', {}).get('name', '')
                        return name if name else 'MergedPack'
            except Exception:
                return 'MergedPack'

        def _sanitize(name):
            """Sanitize pack name for use in filenames."""
            return re.sub(r'[^a-zA-Z0-9_\-]', '_', name).strip('_') or 'MergedPack'

        def _version_from_dir(dirname):
            """Convert 'v2_1_0' -> '2.1.0'; 'vunknown' -> None."""
            ver = dirname[1:] if dirname.startswith('v') else dirname
            ver = ver.replace('_', '.')
            if ver.lower() in ('unknown', 'none', ''):
                return None
            return ver

        bp_count = 0
        rp_count = 0

        for entry in sorted(os.listdir(out)):
            ver_path = os.path.join(out, entry)
            if not os.path.isdir(ver_path) or not entry.startswith('v'):
                continue

            version = _version_from_dir(entry)
            ver_suffix = f'_{version}' if version else ''

            # Move behavior pack
            bp_src = os.path.join(ver_path, f'behavior_pack{ext}')
            if os.path.isfile(bp_src):
                name = _sanitize(_read_pack_name(bp_src))
                bp_dst = os.path.join(bp_dir, f'{name}{ver_suffix}_BP{ext}')
                if os.path.exists(bp_dst):
                    os.remove(bp_dst)
                shutil.move(bp_src, bp_dst)
                bp_count += 1
                logging.info(f"Moved BP -> behavior_packs/{name}{ver_suffix}_BP{ext}")

            # Move resource pack
            rp_src = os.path.join(ver_path, f'resource_pack{ext}')
            if os.path.isfile(rp_src):
                name = _sanitize(_read_pack_name(rp_src))
                rp_dst = os.path.join(rp_dir, f'{name}{ver_suffix}_RP{ext}')
                if os.path.exists(rp_dst):
                    os.remove(rp_dst)
                shutil.move(rp_src, rp_dst)
                rp_count += 1
                logging.info(f"Moved RP -> resource_packs/{name}{ver_suffix}_RP{ext}")

            # Remove the now-empty version directory (and any leftovers)
            try:
                shutil.rmtree(ver_path)
            except Exception:
                pass

        logging.info(f"Restructured output: {bp_count} BP(s) -> behavior_packs/, "
                      f"{rp_count} RP(s) -> resource_packs/")

    # ── Steps 4-16: the actual merge + post-processing ──────────────

    def _run_merge_pipeline(self, files, output_dir):
        """Run the merge and full post-processing pipeline for one group."""

        # Step 4: Process packs (main merging)
        if self._cancel_requested:
            return
        self.progress_update.emit(25)
        self.status_update.emit(_tr("progress.processing_packs", "Processing packs..."))
        self.app._process_packs(files, output_dir)

        # Step 5: Delete manifest files from intermediate zips
        if self._cancel_requested:
            return
        self.progress_update.emit(40)
        self.status_update.emit(_tr("progress.cleaning_manifests", "Cleaning up manifests..."))
        self.app._delete_manifest_files()

        # Step 6: Create manifest
        if self._cancel_requested:
            return
        self.progress_update.emit(50)
        self.status_update.emit(_tr("progress.creating_manifests", "Creating manifests..."))
        self.app._create_manifest(files)

        # Step 7: Move tick and delete functions
        if self._cancel_requested:
            return
        self.progress_update.emit(55)
        self.status_update.emit(_tr("progress.moving_tick_delete",
                                     "Moving tick and delete functions..."))
        self.app._move_tick_and_delete_functions()

        # Step 8: Process script files
        if self._cancel_requested:
            return
        self.progress_update.emit(65)
        self.status_update.emit(_tr("progress.processing_scripts", "Processing script files..."))
        self.app._process_script_files(files)

        # Step 9: Move and cleanup
        if self._cancel_requested:
            return
        self.progress_update.emit(70)
        self.status_update.emit(_tr("progress.moving_cleanup", "Moving and cleaning up..."))
        self.app._move_and_cleanup()

        # Step 10: Update behavior pack with scripts
        if self._cancel_requested:
            return
        self.progress_update.emit(75)
        self.status_update.emit(_tr("progress.updating_bp", "Updating behavior pack..."))
        self.app._update_behavior_pack()

        # Step 11: Merge flipbook textures
        if self._cancel_requested:
            return
        self.progress_update.emit(80)
        self.status_update.emit(_tr("progress.merging_flipbook", "Merging flipbook textures..."))
        self.app._merge_flipbook_textures(files)

        # Step 12: Merge textures list
        if self._cancel_requested:
            return
        self.progress_update.emit(85)
        self.status_update.emit(_tr("progress.merging_textures_list", "Merging textures list..."))
        self.app._merge_textures_list(files)

        # Step 13: Extract and delete zip files
        if self._cancel_requested:
            return
        self.progress_update.emit(90)
        self.status_update.emit(_tr("progress.extracting_textures", "Extracting texture files..."))
        self.app._extract_and_delete_zip_files()

        # Step 14: Move to resource pack
        if self._cancel_requested:
            return
        self.progress_update.emit(95)
        self.status_update.emit(_tr("progress.updating_rp", "Updating resource pack..."))
        self.app._move_to_resource_pack()

        # Step 15: Final cleanup
        if self._cancel_requested:
            return
        self.progress_update.emit(98)
        self.status_update.emit(_tr("progress.final_cleanup", "Final cleanup..."))
        self.app._final_cleanup()

        # Step 16: Package output into selected format
        if self._cancel_requested:
            return
        self.progress_update.emit(99)
        self.status_update.emit(_tr("progress.packaging", "Packaging output..."))
        self.app._package_output()
