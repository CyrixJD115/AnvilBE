# Anvil-MC

Minecraft Bedrock Edition addon merger. Combine multiple `.mcpack` / `.mcaddon` files into one unified pack with smart conflict resolution.

## Features

- Merge any number of packs together
- Smart JSON merging — handles conflicts per file type instead of blindly overwriting
- Detects duplicate entities, items, blocks, recipes, and more — auto-prefixes namespaces or lets you choose
- 11 built-in fixers that patch common addon bugs automatically
- Post-merge patcher that restores missing sections in entity files
- Groups packs by Script API version to keep compatibility
- Pack/unpack folders to `.mcpack` (single or batch)
- Checks if merged packs stay achievement-compatible
- 8 languages built in
- Output as `.mcaddon`, `.mcpack`, or `.zip`
- Dark Minecraft-themed UI

## Requirements

- Python 3.10+
- PySide6 >= 6.6.0
- json5 >= 0.9.14
- Pillow >= 10.0.0

## Getting Started

```bash
uv sync
uv run python main.py
```

Or with pip:

```bash
pip install -e .
anvil-mc
```

## Quick Usage

1. Drop your `.mcpack` / `.mcaddon` files into the **Merger** tab
2. Pick an output folder and format
3. Hit merge
4. Resolve any identifier conflicts if prompted
5. Grab your merged pack from the output folder

There's also a pack utility for converting folders to `.mcpack` and back, a file organizer, and a settings panel for language and defaults.

## Acknowledgements

Based on AutoBE by Frosty. I took the source and completely restructured it — better quality of life, loads of bug fixes, and opened up to the community. Thanks to everyone contributing and helping make this better.

## License

GNU General Public License v3.0 or later (GPL-3.0-or-later).