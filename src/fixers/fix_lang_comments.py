"""
Strip ``//``-prefixed comment lines from ``.lang`` files.

Bedrock's lang parser does not understand ``//`` comments — it treats every
non-empty line as a ``key=value`` pair and logs:
  [Localization][warning] - Invalid lang file format. New line character was
                            found while parsing key: '//...'

Lines whose first non-whitespace characters are ``//`` are replaced with a
blank line so that the overall line count (and any downstream tooling that
relies on it) stays stable.
"""

from __future__ import annotations

TARGETS = ["*.mcpack", "*.mcaddon"]
DESCRIPTION = "Strip unsupported // comment lines from .lang files"


# ── Public API ─────────────────────────────────────────────────────────────

def fix(pack_name: str, filepath: str, content: bytes) -> bytes | None:
    """Return sanitised *bytes* with ``//`` comment lines blanked, or ``None``."""
    if not filepath.endswith(".lang"):
        return None

    try:
        text = content.decode("utf-8", errors="ignore")
    except Exception:
        return None

    lines = text.splitlines(keepends=True)
    output: list[str] = []
    dirty = False

    for line in lines:
        if line.lstrip().startswith("//"):
            output.append("\n")
            dirty = True
        else:
            output.append(line)

    if not dirty:
        return None

    return "".join(output).encode("utf-8")