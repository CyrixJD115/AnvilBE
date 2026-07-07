"""
IdentifierManager — scans packs for identifier conflicts (entities, items, blocks,
loot tables, recipes, animation/render controllers) and provides conflict resolution
with automatic namespace-based prefixing and reference updating.
"""
import os
import json
import re
import logging
from collections import defaultdict


class IdentifierManager:
    """
    Manages identifier conflicts by:
    1. Scanning all identifiers in packs
    2. Detecting conflicts
    3. Generating unique namespaces
    4. Prefixing identifiers
    5. Tracking and updating references
    """

    def __init__(self):
        self.all_identifiers = defaultdict(set)
        self.pack_identifiers = {}
        self.identifier_mapping = {}
        self.pack_namespaces = {}
        self.conflict_map = defaultdict(set)
        self.reference_files = defaultdict(set)
        self.user_resolution = {}

    def scan_pack_identifiers(self, pack_zip, pack_path):
        """
        Scan a pack for all identifiers (entities, items, blocks, loot tables, recipes).
        Returns dict of identifier types and their values.
        """
        identifiers = {
            'entities': set(),
            'items': set(),
            'blocks': set(),
            'loot_tables': set(),
            'recipes': set(),
            'animation_controllers': set(),
            'render_controllers': set(),
            'textures': set()
        }

        try:
            for item_name in pack_zip.namelist():
                nr = item_name.replace('\\', '/')
                if nr.startswith('subpacks/'):
                    continue

                if nr.startswith('entities/') and nr.endswith('.json'):
                    identifiers['entities'].update(
                        self._extract_entity_identifiers(pack_zip, item_name))

                if nr.startswith('items/') and nr.endswith('.json'):
                    identifiers['items'].update(
                        self._extract_item_identifiers(pack_zip, item_name))

                if nr.startswith('blocks/') and nr.endswith('.json'):
                    identifiers['blocks'].update(
                        self._extract_block_identifiers(pack_zip, item_name))

                if nr.startswith('loot_tables/') and nr.endswith('.json'):
                    loot_id = self._extract_loot_table_id(nr)
                    if loot_id:
                        identifiers['loot_tables'].add(loot_id)

                if nr.startswith('recipes/') and nr.endswith('.json'):
                    identifiers['recipes'].update(
                        self._extract_recipe_identifiers(pack_zip, item_name))

                if 'animation_controllers' in nr and nr.endswith('.json'):
                    identifiers['animation_controllers'].update(
                        self._extract_animation_controller_identifiers(pack_zip, item_name))

                if 'render_controllers' in nr and nr.endswith('.json'):
                    identifiers['render_controllers'].update(
                        self._extract_render_controller_identifiers(pack_zip, item_name))

        except Exception as e:
            logging.warning(f"Error scanning identifiers in {pack_path}: {e}")

        return identifiers

    def _extract_entity_identifiers(self, pack_zip, item_name):
        """Extract entity identifiers from an entity JSON file."""
        return self._extract_id_from_json_keys(
            pack_zip, item_name,
            keys=['minecraft:entity', 'minecraft:client_entity'],
            id_field='identifier', exclude={'minecraft:player'})

    def _extract_item_identifiers(self, pack_zip, item_name):
        """Extract item identifiers from an item JSON file."""
        return self._extract_id_from_json_keys(
            pack_zip, item_name,
            keys=['minecraft:item'], id_field='identifier')

    def _extract_block_identifiers(self, pack_zip, item_name):
        """Extract block identifiers from a block JSON file."""
        return self._extract_id_from_json_keys(
            pack_zip, item_name,
            keys=['minecraft:block'], id_field='identifier')

    def _extract_id_from_json_keys(self, pack_zip, item_name, keys, id_field='identifier', exclude=None):
        """Extract identifiers from a JSON file by traversing specific top-level keys."""
        identifiers = set()
        try:
            with pack_zip.open(item_name) as f:
                content = f.read().decode('utf-8', errors='ignore')
                content = re.sub(r'//.*?$|/\*.*?\*/', '', content,
                                  flags=re.MULTILINE | re.DOTALL)
                data = json.loads(content)
                for key in keys:
                    if key in data:
                        desc = data[key].get('description', {})
                        val = desc.get(id_field)
                        if val and (not exclude or val not in exclude):
                            identifiers.add(val)
        except Exception:
            pass
        return identifiers

    def _extract_loot_table_id(self, item_name):
        """Extract loot table identifier from file path."""
        if item_name.startswith('loot_tables/'):
            path_part = item_name[12:]
            if path_part.endswith('.json'):
                path_part = path_part[:-5]
                parts = path_part.split('/')
                if len(parts) >= 2:
                    return f"{parts[0]}:{'/'.join(parts[1:])}"
                elif len(parts) == 1:
                    return f"loot_tables:{parts[0]}"
        return None

    def _extract_recipe_identifiers(self, pack_zip, item_name):
        identifiers = set()
        try:
            with pack_zip.open(item_name) as f:
                content = f.read().decode('utf-8', errors='ignore')
                content = re.sub(r'//.*?$|/\*.*?\*/', '', content,
                                  flags=re.MULTILINE | re.DOTALL)
                data = json.loads(content)
                for key in data:
                    if 'recipe' in key.lower():
                        recipe_data = data[key]
                        if isinstance(recipe_data, dict):
                            rid = recipe_data.get('description', {}).get('identifier')
                            if rid:
                                identifiers.add(rid)
        except Exception:
            pass
        return identifiers

    def _extract_animation_controller_identifiers(self, pack_zip, item_name):
        """Extract identifiers from an animation controller JSON file."""
        return self._extract_keys_with_colon(pack_zip, item_name)

    def _extract_render_controller_identifiers(self, pack_zip, item_name):
        """Extract identifiers from a render controller JSON file."""
        return self._extract_keys_with_colon(pack_zip, item_name)

    def _extract_keys_with_colon(self, pack_zip, item_name):
        """Extract all top-level JSON keys containing ':' as identifiers."""
        identifiers = set()
        try:
            with pack_zip.open(item_name) as f:
                content = f.read().decode('utf-8', errors='ignore')
                content = re.sub(r'//.*?$|/\*.*?\*/', '', content,
                                  flags=re.MULTILINE | re.DOTALL)
                data = json.loads(content)
                for key in data:
                    if ':' in key:
                        identifiers.add(key)
        except Exception:
            pass
        return identifiers

    def detect_conflicts(self, all_pack_identifiers):
        """
        Detect identifier conflicts across all packs.
        *all_pack_identifiers*: dict of pack_path -> identifiers dict
        """
        self.pack_identifiers = all_pack_identifiers

        for pack_path, identifiers in all_pack_identifiers.items():
            for id_type, id_set in identifiers.items():
                for identifier in id_set:
                    ns = identifier.split(':')[0] if ':' in identifier else ''
                    if ns in ('minecraft', 'loot_tables'):
                        continue
                    self.conflict_map[identifier].add(pack_path)

        for idx, pack_path in enumerate(all_pack_identifiers.keys()):
            pack_name = os.path.basename(pack_path).replace('.mcpack', '').replace('.mcaddon', '')
            clean_name = re.sub(r'[^a-zA-Z0-9_]', '_', pack_name)[:20]
            self.pack_namespaces[pack_path] = f"{clean_name}_merge"

    @staticmethod
    def _pack_base_name(pack_path):
        """Strip suffixes so BP/RP halves of the same addon compare equal."""
        name = os.path.basename(pack_path)
        name = re.sub(r'\.(mcpack|mcaddon)$', '', name, flags=re.IGNORECASE)
        name = re.sub(r'_modified$', '', name, flags=re.IGNORECASE)
        name = re.sub(r'_\d+$', '', name)
        name = re.sub(
            r'[_\-\s]*(bp|rp|behaviors?|resources?|behavior[_\-]?pack|resource[_\-]?pack)$',
            '', name, flags=re.IGNORECASE)
        return name.lower()

    def get_conflict_list(self):
        """Return list of (identifier, list of pack_paths) for all conflicted identifiers,
        excluding false conflicts where packs are halves of the same addon."""
        result = []
        for identifier, packs in self.conflict_map.items():
            if len(packs) <= 1:
                continue
            base_names = {self._pack_base_name(p) for p in packs}
            if len(base_names) == 1:
                continue
            result.append((identifier, list(packs)))
        return result

    def set_user_resolution(self, identifier, pack_path_or_none):
        """Set user choice for a conflicted identifier."""
        self.user_resolution[identifier] = pack_path_or_none

    def should_include_definition(self, pack_path, identifier):
        """Return True if this pack's definition of *identifier* should be included."""
        if identifier not in self.user_resolution:
            return True
        keep = self.user_resolution[identifier]
        if keep is None:
            return True
        return pack_path == keep

    def generate_identifier_mappings(self):
        """Generate identifier mappings based on user resolution choices."""
        conflicted = {iid: packs for iid, packs in self.conflict_map.items() if len(packs) > 1}

        for identifier, pack_paths in conflicted.items():
            keep_pack = self.user_resolution.get(identifier)
            if keep_pack is not None:
                for pack_path in pack_paths:
                    self.identifier_mapping[(pack_path, identifier)] = identifier

        logging.info(f"Generated {len(self.identifier_mapping)} identifier mappings")

    def get_new_identifier(self, pack_path, old_identifier):
        """Get the new identifier for a given pack and old identifier."""
        return self.identifier_mapping.get((pack_path, old_identifier), old_identifier)

    def should_rename_identifier(self, identifier):
        """Check if an identifier needs to be renamed (has conflicts)."""
        return len(self.conflict_map.get(identifier, [])) > 1

    def update_json_identifiers(self, json_data, pack_path):
        """Recursively update all identifier references in JSON data."""
        if isinstance(json_data, dict):
            updated = {}
            for key, value in json_data.items():
                if key == 'identifier' and isinstance(value, str):
                    updated[key] = self.get_new_identifier(pack_path, value)
                elif key in ['entity', 'item', 'block', 'loot_table', 'recipe'] and isinstance(value, str):
                    updated[key] = self.get_new_identifier(pack_path, value)
                else:
                    updated[key] = self.update_json_identifiers(value, pack_path)
            return updated
        elif isinstance(json_data, list):
            return [self.update_json_identifiers(item, pack_path) for item in json_data]
        elif isinstance(json_data, str):
            if ':' in json_data and not json_data.startswith('http'):
                new_id = self.get_new_identifier(pack_path, json_data)
                return new_id
        return json_data

    def update_text_identifiers(self, text, pack_path):
        """Update identifier references in text content (scripts, lang files, etc.)."""
        pattern = r'\b([a-zA-Z0-9_]+:[a-zA-Z0-9_\./]+)\b'

        def repl(m):
            return self.get_new_identifier(pack_path, m.group(1))

        return re.sub(pattern, repl, text)
