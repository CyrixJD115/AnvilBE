"""
Universal Compatibility Patcher for AutoBE
Automatically detects and fixes common merge conflicts across all addon types.
"""

import json
import logging
from typing import Dict, List, Any, Optional

_logger = logging.getLogger(__name__)


class UniversalCompatibilityPatcher:
    """
    Automatically patches merged addons to fix common compatibility issues.
    Detects missing critical sections and restores them from source packs.
    """
    
    # Critical sections that should never be missing from entity files
    CRITICAL_ENTITY_SECTIONS = {
        'materials',
        'textures',
        'geometry',
        'render_controllers'
    }
    
    # Sections that should be merged with special handling
    MERGE_WITH_PRESERVE = {
        'materials',
        'textures',
        'geometry'
    }
    
    def __init__(self):
        self.patches_applied = []
    
    def patch_merged_file(
        self,
        merged_data: Dict[str, Any],
        source_data_list: List[Dict[str, Any]],
        file_path: str
    ) -> Dict[str, Any]:
        """
        Patch a merged file by restoring missing critical sections from source files.
        
        Args:
            merged_data: The merged JSON data
            source_data_list: List of source JSON data from original packs
            file_path: Path to the file being patched (for context)
            
        Returns:
            Patched merged data
        """
        if not source_data_list:
            return merged_data
        
        # Detect file type for context-aware patching
        file_type = self._detect_file_type(file_path, merged_data)
        
        # Apply type-specific patches
        if file_type == 'entity':
            merged_data = self._patch_entity_file(merged_data, source_data_list, file_path)
        elif file_type == 'client_entity':
            merged_data = self._patch_client_entity_file(merged_data, source_data_list, file_path)
        elif file_type == 'animation':
            merged_data = self._patch_animation_file(merged_data, source_data_list, file_path)
        elif file_type == 'animation_controller':
            merged_data = self._patch_animation_controller_file(merged_data, source_data_list, file_path)
        
        # Apply universal patches for all file types
        merged_data = self._apply_universal_patches(merged_data, source_data_list, file_path)
        
        return merged_data
    
    def _detect_file_type(self, file_path: str, data: Dict[str, Any]) -> str:
        """Detect the type of file based on path and content."""
        if 'entity' in file_path.lower():
            if 'client_entity' in str(data) or 'minecraft:client_entity' in str(data):
                return 'client_entity'
            return 'entity'
        elif 'animation' in file_path.lower():
            if 'controller' in file_path.lower() or 'animation_controllers' in file_path.lower():
                return 'animation_controller'
            return 'animation'
        return 'generic'
    
    def _patch_entity_file(
        self,
        merged_data: Dict[str, Any],
        source_data_list: List[Dict[str, Any]],
        file_path: str
    ) -> Dict[str, Any]:
        """Patch BP entity files.

        Note: render_controllers/materials/textures/geometry are RP-side
        concerns (minecraft:client_entity), NOT BP entity concerns, so we do
        not flag them as missing here.  See _patch_client_entity_file for the
        RP-side critical-section check.
        """
        return merged_data
    
    def _patch_client_entity_file(
        self,
        merged_data: Dict[str, Any],
        source_data_list: List[Dict[str, Any]],
        file_path: str
    ) -> Dict[str, Any]:
        """Patch client_entity files (like player.entity.json)."""
        if 'minecraft:client_entity' not in merged_data:
            return merged_data
        
        description = merged_data['minecraft:client_entity'].get('description', {})
        
        # Check for missing critical sections
        missing_sections = self.CRITICAL_ENTITY_SECTIONS - set(description.keys())
        
        if missing_sections:
            _logger.debug(f"Client entity file missing critical sections: {missing_sections} in {file_path}")
            
            # Try to restore from source files
            for source_data in source_data_list:
                if 'minecraft:client_entity' in source_data:
                    source_desc = source_data['minecraft:client_entity'].get('description', {})
                    
                    for section in missing_sections:
                        if section in source_desc:
                            if section not in description:
                                # Restore entire section
                                description[section] = source_desc[section]
                                self.patches_applied.append({
                                    'file': file_path,
                                    'type': 'restored_section',
                                    'section': section,
                                    'source': 'original_pack'
                                })
                                _logger.info(f"Restored {section} section in {file_path}")
                            elif isinstance(description[section], dict) and isinstance(source_desc[section], dict):
                                # Merge dictionaries
                                description[section] = self._deep_merge(description[section], source_desc[section])
                                self.patches_applied.append({
                                    'file': file_path,
                                    'type': 'merged_section',
                                    'section': section,
                                    'source': 'original_pack'
                                })
        
        # Special handling for textures - ensure default texture is preserved
        if 'textures' in description:
            for source_data in source_data_list:
                if 'minecraft:client_entity' in source_data:
                    source_desc = source_data['minecraft:client_entity'].get('description', {})
                    if 'textures' in source_desc and 'default' in source_desc['textures']:
                        if 'default' not in description['textures']:
                            description['textures']['default'] = source_desc['textures']['default']
                            self.patches_applied.append({
                                'file': file_path,
                                'type': 'restored_texture',
                                'texture': 'default',
                                'value': source_desc['textures']['default']
                            })
                            _logger.info(f"Restored default texture in {file_path}")
        
        merged_data['minecraft:client_entity']['description'] = description
        return merged_data
    
    def _patch_animation_file(
        self,
        merged_data: Dict[str, Any],
        source_data_list: List[Dict[str, Any]],
        file_path: str
    ) -> Dict[str, Any]:
        """Patch animation files to ensure no animations are lost."""
        if 'format_version' not in merged_data or 'animations' not in merged_data:
            return merged_data
        
        merged_animations = merged_data['animations']
        
        # Collect all animations from source files
        for source_data in source_data_list:
            if 'animations' in source_data:
                for anim_name, anim_data in source_data['animations'].items():
                    if anim_name not in merged_animations:
                        merged_animations[anim_name] = anim_data
                        self.patches_applied.append({
                            'file': file_path,
                            'type': 'restored_animation',
                            'animation': anim_name
                        })
                        _logger.info(f"Restored animation {anim_name} in {file_path}")
        
        merged_data['animations'] = merged_animations
        return merged_data
    
    def _patch_animation_controller_file(
        self,
        merged_data: Dict[str, Any],
        source_data_list: List[Dict[str, Any]],
        file_path: str
    ) -> Dict[str, Any]:
        """Patch animation controller files."""
        if 'format_version' not in merged_data or 'animation_controllers' not in merged_data:
            return merged_data
        
        merged_controllers = merged_data['animation_controllers']
        
        # Collect all controllers from source files
        for source_data in source_data_list:
            if 'animation_controllers' in source_data:
                for ctrl_name, ctrl_data in source_data['animation_controllers'].items():
                    if ctrl_name not in merged_controllers:
                        merged_controllers[ctrl_name] = ctrl_data
                        self.patches_applied.append({
                            'file': file_path,
                            'type': 'restored_controller',
                            'controller': ctrl_name
                        })
                        _logger.info(f"Restored controller {ctrl_name} in {file_path}")
        
        merged_data['animation_controllers'] = merged_controllers
        return merged_data
    
    def _apply_universal_patches(
        self,
        merged_data: Dict[str, Any],
        source_data_list: List[Dict[str, Any]],
        file_path: str
    ) -> Dict[str, Any]:
        """Apply universal patches that work for all file types."""
        # Ensure format_version is present
        if 'format_version' not in merged_data:
            for source_data in source_data_list:
                if 'format_version' in source_data:
                    merged_data['format_version'] = source_data['format_version']
                    self.patches_applied.append({
                        'file': file_path,
                        'type': 'restored_format_version'
                    })
                    break
        
        return merged_data
    
    def _deep_merge(self, base: Dict[str, Any], overlay: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries."""
        result = base.copy()
        
        for key, value in overlay.items():
            if key not in result:
                result[key] = value
            elif isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            elif isinstance(result[key], list) and isinstance(value, list):
                # Merge lists, avoiding duplicates
                result[key] = result[key] + [item for item in value if item not in result[key]]
            else:
                # Keep overlay value (last wins)
                result[key] = value
        
        return result
    
    def get_patch_report(self) -> List[Dict[str, Any]]:
        """Get a report of all patches applied."""
        return self.patches_applied
    
    def clear_patches(self):
        """Clear the patch history."""
        self.patches_applied = []
