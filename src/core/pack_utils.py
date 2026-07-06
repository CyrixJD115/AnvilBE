"""
Pack utilities for Minecraft Bedrock Edition addon management.
Handles pack validation, recursive extraction, and ZIP creation.
"""
import os as _os
import zipfile as _zipfile
import json as _json
import shutil as _shutil
import tempfile as _tempfile
import re as _re
import logging as _logging
from src.core.file_utils import read_text_file_utf8_strip_bom, strip_bom


def is_pack_folder(folder):
    """Return True if *folder* contains manifest.json at its root and has a pack_icon."""
    return _os.path.isfile(_os.path.join(folder, 'manifest.json')) and has_pack_icon(folder)


def has_pack_icon(folder):
    """Check if a folder has a valid pack icon (png/jpg/jpeg)."""
    for ext in ['.png', '.jpg', '.jpeg']:
        if _os.path.isfile(_os.path.join(folder, f'pack_icon{ext}')):
            return True
    return False


def validate_pack_folder(folder_path):
    """
    Validate that a folder is a valid Minecraft pack.
    Returns (is_valid: bool, reason: str).
    """
    manifest_path = _os.path.join(folder_path, 'manifest.json')
    if not _os.path.isfile(manifest_path):
        return False, "manifest.json not found"

    if not has_pack_icon(folder_path):
        _logging.warning(f"Pack folder {folder_path} missing pack_icon")

    try:
        content = read_text_file_utf8_strip_bom(manifest_path)
        cleaned = _re.sub(r'//.*?$|/\*.*?\*/', '', content, flags=_re.MULTILINE | _re.DOTALL)
        manifest = _json.loads(cleaned)

        if 'format_version' not in manifest:
            return False, "manifest.json missing format_version"
        if 'header' not in manifest:
            return False, "manifest.json missing header"
        if 'modules' not in manifest or not manifest['modules']:
            return False, "manifest.json missing or empty modules"

        return True, "Valid pack"
    except _json.JSONDecodeError as e:
        return False, f"Invalid JSON in manifest.json: {e}"
    except Exception as e:
        return False, f"Error validating pack: {e}"


def _try_json_loads(content: str):
    """Parse JSON string, with json5 fallback."""
    cleaned = _re.sub(r'//.*?$|/\*.*?\*/', '', content, flags=_re.MULTILINE | _re.DOTALL)
    try:
        return _json.loads(cleaned)
    except _json.JSONDecodeError:
        try:
            import json5
            return json5.loads(cleaned)
        except Exception:
            return None


def get_pack_manifest_data(file_path):
    """Extract and parse manifest.json from a pack file or folder."""
    try:
        if _os.path.isdir(file_path):
            manifest_path = _os.path.join(file_path, 'manifest.json')
            if _os.path.isfile(manifest_path):
                content = read_text_file_utf8_strip_bom(manifest_path)
                return _try_json_loads(content)
            return None

        with _zipfile.ZipFile(file_path, 'r') as pack_zip:
            manifest_path = None
            for name in pack_zip.namelist():
                name_lower = name.lower()
                if name_lower == 'manifest.json' or name_lower.endswith('/manifest.json'):
                    if name_lower == 'manifest.json':
                        manifest_path = name
                        break
                    if manifest_path is None:
                        manifest_path = name

            if manifest_path:
                with pack_zip.open(manifest_path) as f:
                    content = f.read().decode('utf-8', errors='ignore')
                    return _try_json_loads(content)
    except Exception as e:
        _logging.warning(f"Error reading manifest from {file_path}: {e}")
    return None


def safe_extractall(zf, dest_dir):
    """Like ZipFile.extractall, but normalises backslash paths to forward
    slashes before extraction.

    Source .mcpack files created on Windows may contain backslash separators
    (e.g. ``models\\entity\\file.json``).  On Linux/macOS Python's
    ``extractall`` treats ``\\`` as a literal filename character, producing
    flat files instead of a proper directory tree.  This helper fixes every
    ``ZipInfo.filename`` so that the correct directory structure is created
    regardless of the host OS.
    """
    for member in zf.infolist():
        member.filename = member.filename.replace('\\', '/')
        zf.extract(member, dest_dir)


def recursive_extract_pack(archive_path, dest_dir=None, max_depth=10):
    """
    Recursively extract nested .mcpack/.mcaddon/.zip files until a valid pack
    folder (manifest.json + pack_icon) is found at the root.
    Returns a list of all top-level valid pack folders found.
    """
    if max_depth < 1:
        return []

    if dest_dir is None:
        dest_dir = _tempfile.mkdtemp(prefix='mcpack_unpack_')

    packs_found = []

    try:
        with _zipfile.ZipFile(archive_path, 'r') as z:
            safe_extractall(z, dest_dir)
    except Exception as e:
        _logging.warning(f"Failed to extract {archive_path}: {e}")
        return packs_found

    # Check if dest_dir itself is a valid pack
    if is_pack_folder(dest_dir):
        packs_found.append(dest_dir)
        return packs_found

    # Scan contents for nested archives or pack folders
    for entry in _os.listdir(dest_dir):
        entry_path = _os.path.join(dest_dir, entry)

        if _os.path.isfile(entry_path) and entry.lower().endswith(('.mcpack', '.mcaddon', '.zip')):
            sub_dir = _tempfile.mkdtemp(prefix='mcpack_unpack_')
            packs_found.extend(recursive_extract_pack(entry_path, dest_dir=sub_dir, max_depth=max_depth - 1))
        elif _os.path.isdir(entry_path) and is_pack_folder(entry_path):
            packs_found.append(entry_path)

    return packs_found


def folder_to_mcpack(folder, out_mcpack_path, handle_subpacks=True):
    """
    Zip a folder into .mcpack format.
    If *handle_subpacks* is True, subpacks/ directory is preserved as-is.
    """
    entries = []
    dir_prefixes = set()

    def _add(abs_path):
        arcname = _os.path.relpath(abs_path, folder).replace('\\', '/')
        entries.append((abs_path, arcname))
        parts = arcname.split('/')[:-1]
        for i in range(len(parts)):
            dir_prefixes.add('/'.join(parts[:i + 1]))

    for root, dirs, files in _os.walk(folder):
        if handle_subpacks and 'subpacks' in dirs:
            dirs.remove('subpacks')
        for file in files:
            _add(_os.path.join(root, file))

    if handle_subpacks:
        subpacks_dir = _os.path.join(folder, 'subpacks')
        if _os.path.isdir(subpacks_dir):
            for sub_root, sub_dirs, sub_files in _os.walk(subpacks_dir):
                for sub_file in sub_files:
                    _add(_os.path.join(sub_root, sub_file))

    seen = set()
    with _zipfile.ZipFile(out_mcpack_path, 'w', _zipfile.ZIP_DEFLATED) as zipf:
        for abs_path, arcname in entries:
            if arcname in dir_prefixes or arcname in seen:
                continue
            seen.add(arcname)
            zipf.write(abs_path, arcname)


def zip_pack_folder(folder, output_mcpack_path):
    """Simple zip of a folder into a .mcpack file.

    Normalises all archive paths to forward slashes and skips entries that
    would conflict with a directory path (e.g. a flat backslash-named file
    like ``models\\entity`` colliding with ``models/entity/``).
    """
    entries = []
    dir_prefixes = set()
    for root, dirs, files in _os.walk(folder):
        rel = _os.path.relpath(root, folder)
        for file in files:
            abs_path = _os.path.join(root, file)
            arcname = _os.path.join(rel, file) if rel != '.' else file
            arcname = arcname.replace('\\', '/')
            entries.append((abs_path, arcname))
            parts = arcname.split('/')[:-1]
            for i in range(len(parts)):
                dir_prefixes.add('/'.join(parts[:i + 1]))

    seen = set()
    with _zipfile.ZipFile(output_mcpack_path, 'w', _zipfile.ZIP_DEFLATED) as zf:
        for abs_path, arcname in entries:
            if arcname in dir_prefixes or arcname in seen:
                continue
            seen.add(arcname)
            zf.write(abs_path, arcname)


def find_valid_packs(entry, max_depth=10):
    """
    Recursively find all valid pack folders (manifest.json at root) inside *entry*.
    *entry* can be a directory or .mcpack/.mcaddon/.zip file.
    Returns a list of absolute paths to valid pack folders.
    """
    found = []
    if max_depth < 1:
        return []

    if _os.path.isdir(entry):
        if is_pack_folder(entry):
            found.append(entry)
            return found
        for child in _os.listdir(entry):
            child_path = _os.path.join(entry, child)
            found.extend(find_valid_packs(child_path, max_depth - 1))
        return found

    ext = _os.path.splitext(entry)[1].lower()
    if ext in ('.mcpack', '.mcaddon', '.zip'):
        tempdir = _tempfile.mkdtemp(prefix='mcpacker_temp_')
        try:
            with _zipfile.ZipFile(entry, 'r') as z:
                safe_extractall(z, tempdir)
            for item in _os.listdir(tempdir):
                child_path = _os.path.join(tempdir, item)
                found.extend(find_valid_packs(child_path, max_depth - 1))
            if is_pack_folder(tempdir):
                found.append(tempdir)
        except Exception as e:
            _logging.warning(f"Failed to unzip {entry}: {e}")

    return found


def get_pack_icon_from_zip(zip_file, zip_path=None):
    """
    Extract pack_icon.png (or .jpg/.jpeg) bytes from a ZipFile or folder.
    Returns (bytes, ext) or (None, None).
    """
    if zip_path and _os.path.isdir(zip_path):
        for ext in ['.png', '.jpg', '.jpeg']:
            icon_path = _os.path.join(zip_path, f'pack_icon{ext}')
            if _os.path.isfile(icon_path):
                with open(icon_path, 'rb') as f:
                    return f.read(), ext
        return None, None

    for name in zip_file.namelist():
        base = _os.path.basename(name)
        if base.startswith('pack_icon') and base.endswith(('.png', '.jpg', '.jpeg')):
            ext = _os.path.splitext(base)[1]
            return zip_file.read(name), ext
    return None, None
