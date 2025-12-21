#!/usr/bin/env python3
"""
filter_keywords.py

Small CLI to filter keyword text files using the rules we used interactively.

Features:
- Backup the input file before overwriting
- Configurable lists of substring/whole-word removals
- Built-in defaults (gun-related words, location words, subscription, near, etc.)
- Optional whitelist to keep only lines starting with certain prefixes (e.g., best, top)
- Deduplicate (case-insensitive) option
- Preview and dry-run support

Usage examples (PowerShell):
  python .\python_poster\scripts\filter_keywords.py -i .\python_poster\keywords\kitchenware_filtered.txt --backup
  python .\python_poster\scripts\filter_keywords.py -i keywords.txt -o keywords.clean.txt --dedupe --preview 20

The script writes the filtered result to the input file by default (after backup),
or to `--output` if provided.
"""
import argparse
import re
import shutil
from pathlib import Path
from datetime import datetime


# ===== WHOLE-WORD REMOVAL LISTS =====
# Bất kỳ keyword nào chứa các WHOLE-WORD này sẽ bị remove
# Ví dụ: 'gun' sẽ match "best gun safe" nhưng KHÔNG match "begun"

DEFAULT_GUN_WORDS = [
    'gun', 'rifle', 'riffle', 'pistol', 'revolver', 'shotgun', 'ammo', 'ammunition',
    'bullet', 'bullets', 'magazine', 'mag', 'firearm', 'firearms', 'silencer',
    'suppressor', 'scope', 'sniper', 'ar-15', 'ar15', 'ak-47', 'ak47', 'handgun',
    '9mm', 'magnum', 'armor'
]

DEFAULT_LOCATION_WORDS = [
    'india', 'pakistan', 'bangladesh', 'australia', 'singapore', 'malaysia',
    'uae', 'dubai', 'mexico', 'philippines', 'nz', 'new zealand'
]

DEFAULT_STOP_WORDS = [
    'subscription', 'nearby', 'near', 'shop', 'amazon', 'reddit', 'youtube',
    'way', 'sale', 'manual'
]

# Các từ này chỉ remove khi ĐỨNG ĐỘC LẬP (có space 2 bên hoặc đầu/cuối)
# Ví dụ: " in " hoặc " vs " sẽ bị remove, nhưng "investment" thì KHÔNG
STANDALONE_WORDS = ['in', 'vs']

DEFAULT_QUESTION_PREFIXES = ['what', 'how', 'where', 'who', 'which', 'why']

# ===== SUBSTRING REMOVAL PATTERNS =====
# Remove nếu keyword CHỨA các substring này (không cần whole-word)
DEFAULT_SUBSTRING_REMOVE = ['how', 'troubleshooting', 'mistakes']  # Remove bất kỳ đâu trong keyword


def build_word_regex(words, whole_word=True):
    if not words:
        return None
    escaped = [re.escape(w) for w in words]
    if whole_word:
        pattern = r"\\b(?:" + "|".join(escaped) + r")\\b"
    else:
        pattern = r"(?:" + "|".join(escaped) + r")"
    return re.compile(pattern, flags=re.IGNORECASE)


def build_standalone_regex(words):
    """Build regex for standalone words (surrounded by spaces or at start/end)
    Ví dụ: ' in ' hoặc '^in ' hoặc ' in$' sẽ match, nhưng 'investment' thì KHÔNG
    """
    if not words:
        return None
    escaped = [re.escape(w) for w in words]
    # Match: (start or space) + word + (space or end)
    pattern = r"(?:^|\\s)(?:" + "|".join(escaped) + r")(?=\\s|$)"
    return re.compile(pattern, flags=re.IGNORECASE)


def filter_lines(lines, *, remove_patterns=None, remove_substring_patterns=None,
                 remove_any_substring=None, remove_question_prefix=False,
                 remove_start_digit=False, remove_long_number=False,
                 remove_punctuation_chars=None, keep_prefixes=None,
                 min_words=None, max_words=None):
    """Return (kept_lines, removed_counts)

    Args:
        remove_patterns: List of compiled regex patterns (for whole-word matching)
        remove_substring_patterns: DEPRECATED - use remove_any_substring
        remove_any_substring: List of strings to remove if found ANYWHERE (case-insensitive)
        min_words: Minimum word count (remove if less than this)
        max_words: Maximum word count (remove if more than this)
    """
    kept = []
    counts = {'total': len(lines), 'removed': 0}

    for ln in lines:
        s = ln.rstrip('\\n')

        removed = False

        # Word count filter (check FIRST before other filters)
        if min_words or max_words:
            word_count = len(s.split())
            if min_words and word_count < min_words:
                removed = True
            elif max_words and word_count > max_words:
                removed = True

        # Keep-only prefix (whitelist) - if provided, remove lines not starting with any prefix
        if not removed and keep_prefixes:
            if not any(s.lower().startswith(p.lower()) for p in keep_prefixes):
                removed = True

        # remove patterns (whole-word regex matching)
        if not removed and remove_patterns:
            for pat in remove_patterns:
                if pat.search(s):
                    removed = True
                    break

        # remove substring patterns (case-insensitive substring search)
        if not removed and (remove_substring_patterns or remove_any_substring):
            low = s.lower()
            patterns = remove_any_substring or remove_substring_patterns or []
            for sub in patterns:
                if sub.lower() in low:
                    removed = True
                    break

        # question prefixes
        if not removed and remove_question_prefix:
            if re.match(r'^(?:' + '|'.join(DEFAULT_QUESTION_PREFIXES) + r')\\b', s, flags=re.IGNORECASE):
                removed = True

        # start-with-digit
        if not removed and remove_start_digit:
            if re.match(r'^\\d', s):
                removed = True

        # long numeric sequences
        if not removed and remove_long_number:
            if re.search(r'\\d{5,}', s):
                removed = True

        # punctuation chars (if any) - remove line if it contains any of these
        if not removed and remove_punctuation_chars:
            if any(ch in s for ch in remove_punctuation_chars):
                removed = True

        if not removed:
            kept.append(s)
        else:
            counts['removed'] += 1

    return kept, counts


def dedupe_preserve_order(lines):
    seen = set()
    out = []
    for s in lines:
        k = s.lower()
        if k in seen:
            continue
        seen.add(k)
        out.append(s)
    return out


def main():
    p = argparse.ArgumentParser(description='Filter keyword files (backup before overwrite)')
    p.add_argument('-i', '--input', required=True, help='Input keywords file (one per line)')
    p.add_argument('-o', '--output', help='Output file (if omitted, overwrite input after backup)')
    p.add_argument('--no-backup', action='store_true', help='Do not create a backup')
    p.add_argument('--dry-run', action='store_true', help='Do everything but do not write output')
    p.add_argument('--preview', type=int, default=10, help='Number of lines to preview after filtering')
    p.add_argument('--dedupe', action='store_true', help='Remove duplicate lines (case-insensitive)')
    p.add_argument('--keep-prefixes', help='Comma-separated prefixes to keep (e.g., best,top)')
    p.add_argument('--remove-in', action='store_true', help='Also remove whole-word "in" (dangerous)')
    args = p.parse_args()

    inp = Path(args.input)
    if not inp.exists():
        print(f"Input not found: {inp}")
        return

    out_path = Path(args.output) if args.output else inp

    # Read lines
    with inp.open('r', encoding='utf-8', errors='replace') as fh:
        raw_lines = fh.readlines()

    # Build WHOLE-WORD regex patterns
    # Các từ trong DEFAULT_GUN_WORDS, DEFAULT_LOCATION_WORDS, DEFAULT_STOP_WORDS
    # sẽ được match theo whole-word (\\b word \\b)
    gun_pat = build_word_regex(DEFAULT_GUN_WORDS, whole_word=True)
    location_pat = build_word_regex(DEFAULT_LOCATION_WORDS, whole_word=True)
    stop_pat = build_word_regex(DEFAULT_STOP_WORDS, whole_word=True)

    # STANDALONE patterns (chỉ match khi từ ĐỨNG ĐỘC LẬP - có space hoặc đầu/cuối)
    standalone_pat = build_standalone_regex(STANDALONE_WORDS)

    remove_patterns = [p for p in (gun_pat, location_pat, stop_pat, standalone_pat) if p]

    # SUBSTRING matching (remove nếu chứa từ này BẤT KỲ ĐÂU)
    # 'how', 'troubleshooting' sẽ remove ngay cả khi ở giữa keyword
    remove_any_substring = DEFAULT_SUBSTRING_REMOVE.copy()

    if args.remove_in:
        # Note: 'in' đã có trong STANDALONE_WORDS (standalone), flag này deprecated
        pass

    keep_prefixes = [s.strip() for s in args.keep_prefixes.split(',')] if args.keep_prefixes else None

    # Apply filters
    filtered, counts = filter_lines(
        raw_lines,
        remove_patterns=remove_patterns,
        remove_any_substring=remove_any_substring,
        remove_question_prefix=True,  # Remove lines starting with what/where/who/which/why
        remove_start_digit=True,
        remove_long_number=True,
        remove_punctuation_chars=['.'],
        keep_prefixes=keep_prefixes,
        min_words=3,  # Chỉ giữ keyword có >= 3 từ
        max_words=6,  # Chỉ giữ keyword có <= 6 từ
    )

    # Dedupe if requested
    before_dedup = len(filtered)
    if args.dedupe:
        filtered = dedupe_preserve_order(filtered)

    # Summary
    print(f"Input lines: {counts['total']}")
    print(f"Removed by filters (approx): {counts['removed']}")
    if args.dedupe:
        print(f"After dedupe: {len(filtered)} (removed {before_dedup - len(filtered)} duplicates)")
    else:
        print(f"Output lines: {len(filtered)}")

    # Preview
    print('\\n--- Preview ---')
    for line in filtered[: args.preview]:
        print(line)

    # Write output (unless dry-run)
    if args.dry_run:
        print('\\nDry-run: no files written')
        return

    # Backup
    if not args.no_backup and out_path.exists():
        ts = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        bak = out_path.with_name(out_path.name + f'.pre_filter_{ts}.bak')
        shutil.copy2(out_path, bak)
        print(f'Backup written: {bak}')

    # Write file
    with out_path.open('w', encoding='utf-8') as fh:
        for line in filtered:
            fh.write(line.rstrip('\n') + '\n')

    print(f'Wrote filtered output to: {out_path}')


if __name__ == '__main__':
    main()