"""
MergeWorkerThread — runs the complete merge pipeline in a background thread
and communicates progress via Qt signals.
"""
import logging as _logging
import traceback
from PySide6.QtCore import QThread, Signal


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
        Follows the merge workflow from the original AutoBE implementation.
        """
        try:
            # Step 1: Validate files
            if self._cancel_requested:
                self.finished.emit(False, "Cancelled")
                return
            self.progress_update.emit(5)
            self.status_update.emit("Validating files...")
            if not self.app._validate_files(show_gui=False):
                self.finished.emit(False, "Validation failed")
                return

            # Step 2: Extract and store highest versions
            if self._cancel_requested:
                self.finished.emit(False, "Cancelled")
                return
            self.progress_update.emit(10)
            self.status_update.emit("Extracting version information...")
            self.app._extract_and_store_highest_versions()

            # Step 3: Check compatibility
            if self._cancel_requested:
                self.finished.emit(False, "Cancelled")
                return
            self.progress_update.emit(15)
            self.status_update.emit("Checking compatibility...")
            self.app._check_compatibility(show_gui=False)

            # Step 4: Process packs (main merging pipeline)
            if self._cancel_requested:
                self.finished.emit(False, "Cancelled")
                return
            self.progress_update.emit(25)
            self.status_update.emit("Processing packs...")
            self.app._process_packs(self.files, self.output_dir)

            # Step 5: Delete manifest files from intermediate zips
            if self._cancel_requested:
                self.finished.emit(False, "Cancelled")
                return
            self.progress_update.emit(40)
            self.status_update.emit("Cleaning up manifests...")
            self.app._delete_manifest_files()

            # Step 6: Create manifest
            if self._cancel_requested:
                self.finished.emit(False, "Cancelled")
                return
            self.progress_update.emit(50)
            self.status_update.emit("Creating manifests...")
            self.app._create_manifest()

            # Step 7: Move tick and delete functions
            if self._cancel_requested:
                self.finished.emit(False, "Cancelled")
                return
            self.progress_update.emit(55)
            self.status_update.emit("Moving tick and delete functions...")
            self.app._move_tick_and_delete_functions()

            # Step 8: Process script files
            if self._cancel_requested:
                self.finished.emit(False, "Cancelled")
                return
            self.progress_update.emit(65)
            self.status_update.emit("Processing script files...")
            self.app._process_script_files(self.files)

            # Step 9: Move and cleanup
            if self._cancel_requested:
                self.finished.emit(False, "Cancelled")
                return
            self.progress_update.emit(70)
            self.status_update.emit("Moving and cleaning up...")
            self.app._move_and_cleanup()

            # Step 10: Update behavior pack with scripts
            if self._cancel_requested:
                self.finished.emit(False, "Cancelled")
                return
            self.progress_update.emit(75)
            self.status_update.emit("Updating behavior pack...")
            self.app._update_behavior_pack()

            # Step 11: Merge flipbook textures
            if self._cancel_requested:
                self.finished.emit(False, "Cancelled")
                return
            self.progress_update.emit(80)
            self.status_update.emit("Merging flipbook textures...")
            self.app._merge_flipbook_textures(self.files)

            # Step 12: Merge textures list
            if self._cancel_requested:
                self.finished.emit(False, "Cancelled")
                return
            self.progress_update.emit(85)
            self.status_update.emit("Merging textures list...")
            self.app._merge_textures_list(self.files)

            # Step 13: Extract and delete zip files
            if self._cancel_requested:
                self.finished.emit(False, "Cancelled")
                return
            self.progress_update.emit(90)
            self.status_update.emit("Extracting texture files...")
            self.app._extract_and_delete_zip_files()

            # Step 14: Move to resource pack
            if self._cancel_requested:
                self.finished.emit(False, "Cancelled")
                return
            self.progress_update.emit(95)
            self.status_update.emit("Updating resource pack...")
            self.app._move_to_resource_pack()

            # Step 15: Final cleanup
            if self._cancel_requested:
                self.finished.emit(False, "Cancelled")
                return
            self.progress_update.emit(98)
            self.status_update.emit("Final cleanup...")
            self.app._final_cleanup()

            self.progress_update.emit(100)
            self.status_update.emit("Complete!")
            self.finished.emit(True, "All packs merged successfully!")

        except Exception as e:
            _logging.error(f"Error during processing: {e}", exc_info=True)
            self.error.emit(str(e))
            self.finished.emit(False, f"An error occurred: {e}")
