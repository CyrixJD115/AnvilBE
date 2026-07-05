"""Split AutoBE.py into topping, def-group files (≤700 lines each), and footing."""

import ast
import os
import sys

MAX_LINES = 980


def split_python_file(filepath, out_dir=None):
    if out_dir is None:
        out_dir = os.path.dirname(os.path.abspath(__file__))

    with open(filepath, 'r', encoding='utf-8') as f:
        source = f.read()

    lines = source.splitlines(keepends=True)

    tree = ast.parse(source)

    # Collect top-level definitions
    defs = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            start = node.lineno - 1
            end = node.end_lineno
            size = end - start
            defs.append((start, end, node.name, type(node).__name__, size, node))

    if not defs:
        print("No top-level class/function definitions found.")
        return

    first_def_lineno = defs[0][0]
    last_def_end_lineno = defs[-1][1]

    base = os.path.splitext(os.path.basename(filepath))[0]

    # --- Topping ---
    topping = ''.join(lines[:first_def_lineno])
    topping_path = os.path.join(out_dir, f'{base}_topping.py')
    with open(topping_path, 'w', encoding='utf-8') as f:
        f.write(topping)
    print(f'Wrote: {topping_path} ({len(topping.splitlines())} lines)')

    # --- Helper: split a large class into method-group chunks ---
    def split_large_class(start, end, name, class_node):
        """Split a class into chunks of ≤MAX_LINES at method boundaries."""
        body_nodes = []
        for child in ast.iter_child_nodes(class_node):
            # Only split at method defs (skip assignments, etc. — they stay with the prior chunk)
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                body_nodes.append(child)

        # Build chunks: each chunk starts with 'class ClassName:' + some methods
        chunks = []
        current_methods = []
        current_line_count = 1  # 'class ClassName:' line

        def emit_chunk(methods, is_last=False):
            if not methods:
                return
            c_start = methods[0].lineno - 1
            c_end = methods[-1].end_lineno
            # Include the class header line + trailing whitespace before first method
            header_line = class_node.lineno - 1
            chunk_source = lines[header_line:header_line + 1]  # 'class ClassName:\n'
            # Include any decorators/blank lines between header and first method
            pre_method = c_start
            chunk_source += lines[header_line + 1:c_start]
            chunk_source += lines[c_start:c_end]
            if not is_last:
                # Find gap to next method group's first method (if any)
                pass
            chunks.append((c_start, c_end, chunk_source))

        chunk_sources = []

        header_line_idx = class_node.lineno - 1
        prev_end = header_line_idx + 1  # line after class header — start of non-overlapping content

        i = 0
        while i < len(body_nodes):
            chunk_methods = []
            chunk_size = 0
            j = i
            while j < len(body_nodes):
                m_start = body_nodes[j].lineno - 1
                m_end = body_nodes[j].end_lineno
                m_size = m_end - m_start
                gap = m_start - (body_nodes[j-1].end_lineno if j > i else prev_end)
                if chunk_size + gap + m_size > MAX_LINES and chunk_methods:
                    break
                chunk_methods.append(body_nodes[j])
                chunk_size += gap + m_size
                j += 1

            last_m = chunk_methods[-1]
            c_end = last_m.end_lineno

            # Source: class header + ONLY new content from prev_end to c_end
            src = ''.join(lines[header_line_idx:header_line_idx + 1])
            src += ''.join(lines[prev_end:c_end])
            chunk_sources.append(src)

            prev_end = c_end
            i = j

        return chunk_sources

    # --- Build groups, splitting large defs ---
    groups = []  # list of (start_line, end_line, source_strings)

    current_group_start = None
    current_group_end = None
    current_group_sources = []
    current_group_size = 0

    def flush_group():
        nonlocal current_group_start, current_group_end, current_group_sources, current_group_size
        if current_group_sources:
            groups.append((current_group_start, current_group_end, current_group_sources))
        current_group_start = None
        current_group_end = None
        current_group_sources = []
        current_group_size = 0

    for d in defs:
        start, end, name, kind, size, node = d

        if size > MAX_LINES and kind == 'ClassDef':
            # Flush current group first, then split the class
            flush_group()
            c_sources = split_large_class(start, end, name, node)
            for src in c_sources:
                groups.append((None, None, [src]))
            continue

        if size > MAX_LINES and kind == 'FunctionDef':
            # Lone large function — flush and put it solo
            flush_group()
            groups.append((start, end, [''.join(lines[start:end])]))
            continue

        # Small def: try to add to current group
        # Include gap between current_group_end and this def's start
        gap = start - current_group_end if current_group_end is not None else 0
        if current_group_sources and current_group_size + gap + size > MAX_LINES:
            flush_group()

        if current_group_sources is None or not current_group_sources:
            current_group_start = start

        # Add the gap before this def (if any) and the def itself
        if current_group_end is not None and gap > 0:
            current_group_sources.append(''.join(lines[current_group_end:start]))
            current_group_size += gap

        current_group_sources.append(''.join(lines[start:end]))
        current_group_size += size
        current_group_end = end

    flush_group()

    # --- Write def group files ---
    for g_idx, (g_start, g_end, sources) in enumerate(groups):
        full_source = ''.join(sources)
        # Trim trailing whitespace-only lines for clean output
        group_path = os.path.join(out_dir, f'{base}_defs_{g_idx+1:02d}.py')
        with open(group_path, 'w', encoding='utf-8') as f:
            f.write(full_source)
        line_count = len(full_source.splitlines())
        # Extract def names from the source for logging
        print(f'Wrote: {group_path} ({line_count} lines)')

    # --- Footing ---
    footing = ''.join(lines[last_def_end_lineno:])
    footing_path = os.path.join(out_dir, f'{base}_footing.py')
    with open(footing_path, 'w', encoding='utf-8') as f:
        f.write(footing)
    print(f'Wrote: {footing_path} ({len(footing.splitlines())} lines)')


if __name__ == '__main__':
    target = sys.argv[1] if len(sys.argv) > 1 else None
    if target is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        target = os.path.join(os.path.dirname(script_dir), 'AutoBE.py')
    split_python_file(target)
