"""
Help tab — built-in documentation browser for Anvil-MC.
Provides sections on overview, getting started, merging, errors, and best practices.
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QLabel
from PySide6.QtCore import Qt


_HELP_CONTENT = """
<h1 style='color: #7CBD4D;'>Anvil-MC — Help &amp; Documentation</h1>

<h2 style='color: #5CE3E6;'>Overview</h2>
<p>Anvil-MC is a Minecraft Bedrock Edition addon merging tool. It combines multiple
behavior packs and resource packs into unified output packs, handling JSON merging,
conflict resolution, script concatenation, and automatic compatibility fixes.</p>

<h2 style='color: #5CE3E6;'>Getting Started</h2>
<ol>
  <li><b>Add Files</b> — Click "Add Files" on the Merger tab to select .mcpack, .mcaddon,
      or .zip files. You can also select folders containing unpacked packs.</li>
  <li><b>Check Packs</b> — Click "Check Packs" to scan your selected packs for
      script API version grouping and compatibility information.</li>
  <li><b>Select Output</b> — Choose where the merged packs should be saved.</li>
  <li><b>Start Merging</b> — Click "Start Merging" to begin the merge process.
      Progress is shown on the progress bar.</li>
</ol>

<h2 style='color: #5CE3E6;'>The Merging Process</h2>
<p>The merge pipeline processes packs in the following order:</p>
<ol>
  <li><b>Validation</b> — Each pack is checked for valid manifest.json and structure.</li>
  <li><b>Version Tracking</b> — Highest format versions are recorded across all packs.</li>
  <li><b>Compatibility Check</b> — Achievement compatibility is evaluated.</li>
  <li><b>Processing</b> — Files are extracted, categorized (BP/RP), and merged:</li>
  <ul>
    <li>JSON files are merged using the UniversalJsonMerger with conflict detection.</li>
    <li>Script files are concatenated with duplicate removal.</li>
    <li>.lang files are merged key-by-key.</li>
    <li>Binary assets (textures, sounds) use first-wins strategy.</li>
    <li>Entity, item, and block files are intelligently merged by identifier.</li>
  </ul>
  <li><b>Manifest Creation</b> — A unified manifest is generated for output packs.</li>
  <li><b>ExtendedBE Fixers</b> — Per-addon fixers are applied for compatibility.</li>
  <li><b>Finalization</b> — Output packs are zipped and cleaned up.</li>
</ol>

<h2 style='color: #5CE3E6;'>Identifier Conflict Resolution</h2>
<p>When two packs define the same identifier (entity, item, block, etc.), the
conflict resolution dialog will appear during merging. You can choose to:</p>
<ul>
  <li><b>Keep all (deep merge)</b> — Both definitions are merged together. This is
      recommended when the same identifier comes from BP/RP halves of the same addon.</li>
  <li><b>Keep one pack's definition</b> — Select which pack's definition to use.
      The other pack's definition is excluded from the output.</li>
</ul>

<h2 style='color: #5CE3E6;'>Script API Version Groups</h2>
<p>Packs with different @minecraft/server script API versions cannot be merged into
a single pack. Anvil-MC groups packs by their script API version and creates
separate output subfolders for each group. Common files (player.json, HUD, etc.)
are unified across groups automatically.</p>

<h2 style='color: #5CE3E6;'>Subpack Selection</h2>
<p>Some packs contain multiple subpack variants (e.g., different resolution textures).
When such packs are detected, a subpack selection dialog will let you choose which
variant to include in the merge.</p>

<h2 style='color: #5CE3E6;'>ExtendedBE Fixers</h2>
<p>The ExtendedBE framework automatically detects and fixes common issues in addon packs:</p>
<ul>
  <li>Old item/block format conversion</li>
  <li>Missing item/block definitions</li>
  <li>Empty JSON files</li>
  <li>Stub animation controllers</li>
  <li>Misplaced files</li>
  <li>Outdated sound definitions</li>
  <li>And more...</li>
</ul>

<h2 style='color: #5CE3E6;'>MCPacker Tab</h2>
<p>The MCPacker tab lets you bundle unpacked folders into .mcpack format.
Select a folder containing a valid pack structure (with manifest.json), choose
an output location, and click Start.</p>

<h2 style='color: #5CE3E6;'>List Maker Tab</h2>
<p>The List Maker tab organizes your pack files by creation date and groups them
by Script API version. Use "Organize by Date" to sort files chronologically,
and "Export List" to save the organization to a file.</p>

<h2 style='color: #5CE3E6;'>Error Handling</h2>
<p>If an error occurs during merging:</p>
<ol>
  <li>Check the error message shown in the dialog.</li>
  <li>Look at the <code>error_log.txt</code> file in the app data directory for detailed logs.</li>
  <li>Ensure all packs have valid <code>manifest.json</code> files.</li>
  <li>Make sure you have write permissions for the output directory.</li>
</ol>

<h2 style='color: #5CE3E6;'>Best Practices</h2>
<ul>
  <li>Always check packs before merging to avoid script version conflicts.</li>
  <li>Use the "Keep all (deep merge)" option for BP/RP pairs of the same addon.</li>
  <li>Review the merge log for warnings about variable redefinitions.</li>
  <li>Keep your source packs organized in folders for easy re-merging.</li>
</ul>

<hr style='border: 1px solid #3D3D3D;'>

<p style='color: #606060;'><i>Anvil-MC — Minecraft Bedrock Edition Addon Merger</i></p>
"""


class HelpTab(QWidget):
    """
    Tab displaying built-in documentation and help content.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        self._text_edit = QTextEdit()
        self._text_edit.setReadOnly(True)
        self._text_edit.setHtml(_HELP_CONTENT)
        self._text_edit.setStyleSheet("""
            QTextEdit {
                background-color: #1A1A1A;
                color: #B0B0B0;
                border: 2px solid #3D3D3D;
                padding: 12px;
                font-size: 10pt;
            }
        """)
        layout.addWidget(self._text_edit)
