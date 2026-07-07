# Anvil-MC

Minecraft Bedrock Edition addon merger — merge multiple `.mcpack` / `.mcaddon` behavior and resource packs into a single unified addon with intelligent conflict resolution.

## Features

- **Multi-pack merging** — combine any number of packs into one
- **Context-aware JSON merging** — per-file-type strategies (version keep-highest, array concatenation, dict first-wins, recursive merge) rather than blind overwrite
- **Identifier conflict resolution** — detects duplicate entities, items, blocks, recipes, loot tables, animation/render controllers, and textures; auto-prefixes namespaces or lets you choose
- **11 built-in fixers** — patches common source-addon bugs (empty JSON files, deprecated `run_command`, missing definitions, outdated block/item formats, invalid sounds, stub animation controllers, and more)
- **Universal compatibility patcher** — post-merge auto-restoration of missing critical sections in entity files
- **Merge by Script API version** — groups packs by version to maintain compatibility; output organized into versioned folders
- **Pack/unpack utility** — convert between folders and `.mcpack` (single or batch)
- **Achievement-safe checking** — verifies merged packs support achievements
- **Internationalization** — 8 languages (English, Spanish, Chinese, Indonesian, Russian, Portuguese, French, German)
- **Multiple output formats** — `.mcaddon`, `.mcpack`, or `.zip`
- **Minecraft-themed dark UI** — custom QSS stylesheet with bundled fonts

## Requirements

- Python 3.10+
- PySide6 >= 6.6.0
- json5 >= 0.9.14
- Pillow >= 10.0.0

## Installation

### With uv (recommended)

```bash
uv sync
uv run python main.py
```

### With pip

```bash
pip install -e .
anvil-mc
```

Or directly:

```bash
python main.py
```

## macOS Build

Pre-built `.app` bundles are available from GitHub Releases.

### First run — bypass Gatekeeper

macOS may block the app because it isn't signed with an Apple Developer account. To fix:

1. Extract the downloaded zip to get `Anvil-MC.app`
2. Open Terminal in the folder containing `Anvil-MC.app` (in Finder: right-click the folder → **New Terminal at Folder**)
3. Run:
   ```bash
   xattr -dr com.apple.quarantine Anvil-MC.app
   ```
4. Now double-click `Anvil-MC.app` to launch normally

> **Alternative** (no terminal): right-click `Anvil-MC.app` → **Open**, then click **Open** in the dialog. This only needs to be done once.

## Usage

1. **Merger tab** — add `.mcpack` / `.mcaddon` files (drag-drop or via buttons)
2. Pick an output directory and format
3. Optionally enable **Merge by version** or **Modpack organization**
4. Click merge — the pipeline validates, fixes, merges, and packages
5. Resolve any identifier conflicts when prompted
6. Find the merged output in your chosen directory

Additional tools:
- **MCPacker tab** — pack folders into `.mcpack` or unpack them
- **List Maker tab** — organize files chronologically by version group
- **Settings tab** — language, output defaults, feature toggles
- **Console tab** — live color-coded log output
- **Help tab** — built-in documentation

## Project Structure

```
src/
  app.py                  # Main window & merge orchestration
  core/
    merger.py             # UniversalJsonMerger — context-aware JSON merging
    pack_utils.py         # Pack validation, zip extraction/creation
    file_utils.py         # BOM stripping, safe JSON reading
    identifier_manager.py # Identifier conflict detection & namespace resolution
    i18n.py               # Internationalization system
  fixers/
    __init__.py           # Fixer loader
    excel_manager.py      # Excel/CSV addon organization
    universal_compatibility.py  # Post-merge patcher
    fix_*.py              # 11 per-addon fixers
  ui/
    merger_tab.py         # Primary merge interface
    mcpacker_tab.py       # Pack/unpack utility
    list_maker_tab.py     # File organizer
    settings_tab.py       # Application settings
    help_tab.py           # Documentation browser
    console_tab.py        # Live log panel
    dialogs.py            # Conflict resolution & about dialogs
    widgets.py            # Custom UI widgets
  workers/
    merge_worker.py       # Background merge pipeline thread
  theme/                  # QSS stylesheet, fonts, icons
version.yaml              # Version number (what you see in the app)
main.py                   # Entry point
locales/                  # Translation JSON files
resources/                # Help content HTML
```

## License

GNU General Public License v3.0 or later (GPL-3.0-or-later).
