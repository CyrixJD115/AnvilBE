"""
File I/O utilities for Minecraft pack handling.
Provides BOM stripping, safe decoding, and robust file read/write helpers.
"""
import os as _os
import json as _json
import logging as _logging


def strip_bom(text):
    """Strip Unicode BOM (\\ufeff) and UTF-8 BOM interpreted as latin-1 (\\xef\\xbb\\xbf)."""
    if text.startswith('\ufeff'):
        text = text[1:]
    if text.startswith('\xef\xbb\xbf'):
        text = text[3:]
    if text.startswith('ï»¿'):
        text = text[3:]
    return text


def read_text_file_utf8_strip_bom(path):
    """Read a UTF-8 text file and strip any BOM prefix."""
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    return strip_bom(text)


def write_text_file_utf8(path, content):
    """Write content to a file with UTF-8 encoding."""
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)


def safe_decode(byte_data):
    """Safely decode bytes to string, falling back to latin-1 on failure."""
    try:
        return byte_data.decode('utf-8')
    except UnicodeDecodeError:
        try:
            return byte_data.decode('latin-1')
        except UnicodeDecodeError:
            return byte_data.decode('utf-8', errors='replace')


def read_json_safe(path):
    """Read and parse a JSON file, stripping comments first."""
    try:
        content = read_text_file_utf8_strip_bom(path)
        # Strip single-line and multi-line comments
        import re
        cleaned = re.sub(r'//.*?$|/\*.*?\*/', '', content, flags=re.MULTILINE | re.DOTALL)
        return _json.loads(cleaned)
    except Exception as e:
        _logging.warning(f"Failed to read JSON from {path}: {e}")
        return None


def sanitize_filename(filename):
    """Sanitize a filename to be safe for the filesystem."""
    import re
    return re.sub(r'[^\w\-_\. ]', '_', filename)
