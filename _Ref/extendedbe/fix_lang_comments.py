"""
Fixes .lang files that use // as comment lines. Bedrock's lang parser does
not support // comments — it treats every non-empty line as a key=value pair
and logs:
  [Localization][warning] - Invalid lang file format. New line character was
                            found while parsing key: '//...'

The fix: strip any line whose first non-whitespace characters are //
(replacing it with an empty line so line numbers in other tooling stay stable).
"""

TARGETS = ["*.mcpack", "*.mcaddon"]
DESCRIPTION = "Strip unsupported // comment lines from .lang files"


def fix(pack_name, filepath, content):
    if not filepath.endswith(".lang"):
        return None
    try:
        text = content.decode("utf-8", errors="ignore")
    except Exception:
        return None

    lines = text.splitlines(keepends=True)
    cleaned = []
    changed = False
    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith("//"):
            cleaned.append("\n")
            changed = True
        else:
            cleaned.append(line)

    if not changed:
        return None
    return "".join(cleaned).encode("utf-8")
