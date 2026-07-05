#!/usr/bin/env python3
"""
AutoBE activation key generator.
Generates keys in the same style as existing AutoBE keys (special chars + A,u,t,o,B,E embedded).
Keys are CSV-safe and avoid characters that often break copy-paste or GitHub CSV.
Output: one key per line, ready to paste into keys.csv (one key per row).
"""
import random
import sys

# Chars that look "key-like" and are safe in CSV (no comma, no newline).
# Avoid double-quote so keys don't need escaping in CSV and copy-paste is reliable.
CHARS = (
    "abcdefghijklmnopqrstuvwxyz"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789"
    r"!@#$%^&*()_+-=[]{}|;':`~<>?\/"
    "."
)

# Letters that must appear in order to spell "AutoBE" (embedded in the key)
AUTOBE_LETTERS = ["A", "u", "t", "o", "B", "E"]


def generate_one_key(length_min=14, length_max=28, embed_autobe=True, fixed_length=None):
    """
    Generate a single key with optional "AutoBE" letters in order (scattered).
    If fixed_length is set, all keys have that length; else length is random between min and max.
    """
    if fixed_length is not None:
        length = max(fixed_length, len(AUTOBE_LETTERS) + 4)
    else:
        length = random.randint(length_min, length_max)
        if embed_autobe and length < len(AUTOBE_LETTERS):
            length = len(AUTOBE_LETTERS) + random.randint(4, 12)

    # Build key as list of chars so we can insert AUTOBE at random positions
    key_chars = [random.choice(CHARS) for _ in range(length)]

    if embed_autobe and length >= len(AUTOBE_LETTERS):
        # Pick random positions for A, u, t, o, B, E (must stay in order, scattered)
        positions = sorted(random.sample(range(length), len(AUTOBE_LETTERS)))
        for i, pos in enumerate(positions):
            key_chars[pos] = AUTOBE_LETTERS[i]

    return "".join(key_chars)


def main():
    count = 20
    fixed_length = None
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--length" and i + 1 < len(args):
            try:
                fixed_length = int(args[i + 1])
                i += 2
                continue
            except ValueError:
                pass
        try:
            count = int(args[i])
        except (ValueError, IndexError):
            pass
        i += 1

    print("AutoBE key generator – paste these into keys.csv (one per row):")
    print("=" * 60)
    keys = []
    for _ in range(count):
        k = generate_one_key(embed_autobe=True, fixed_length=fixed_length)
        keys.append(k)
        print(k)
    print("=" * 60)
    length_note = f" (length {len(keys[0])})" if keys and fixed_length is not None else ""
    print(f"Generated {len(keys)} keys{length_note}. Add them to keys.csv in your repo (one key per line).")


if __name__ == "__main__":
    main()
