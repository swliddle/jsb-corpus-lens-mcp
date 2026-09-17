#!/usr/bin/env python3
"""
Book of Mormon FULL Extraction Script
======================================
Parses the Project Gutenberg 1830 text and creates per-chapter files for ALL books:
  1. 1830 Edition:   1830-03-26-{Book}-{ch}-1830.txt  (with diff headers)
  2. Original:       {date}-{Book}-{ch}-Original.txt

Books: 1Nephi(22), 2Nephi(33), Jacob(7), Enos(1), Jarom(1), Omni(1),
       WordsOfMormon(1), Mosiah(29), Alma(63), Helaman(16), 3Nephi(30),
       4Nephi(1), Mormon(9), Ether(15), Moroni(10)
Total: 239 chapters × 2 editions = 478 files
"""

import os
import re

# === CONFIGURATION ===

GUTENBERG_FILE = "/Users/ericdenna/.gemini/antigravity/brain/5c8f70ce-7a1f-4a3d-b193-b3f80041c992/.system_generated/steps/75/content.md"

OUTPUT_DIR = "/Users/ericdenna/Library/CloudStorage/GoogleDrive-eric.denna@gmail.com/My Drive/! AAA Personal - WIP/! Joseph the Prophet/JSB - WIP/JSB Doctrinal Learning  over time/JS Revelations by Date"

# === BOOK DEFINITIONS ===
# (gutenberg_header_pattern, file_prefix, chapter_pattern, num_chapters, preamble_book_name)

BOOKS = [
    {
        "name": "1 Nephi",
        "prefix": "1Nephi",
        "chapters": 22,
        "header": r"THE FIRST BOOK OF NEPHI HIS REIGN AND MINISTRY \(1 Nephi\)",
        "chapter_pattern": "1 Nephi Chapter",
        "preamble_name": "THE FIRST BOOK OF NEPHI HIS REIGN AND MINISTRY (1 Nephi)",
    },
    {
        "name": "2 Nephi",
        "prefix": "2Nephi",
        "chapters": 33,
        "header": r"THE SECOND BOOK OF NEPHI",
        "chapter_pattern": "2 Nephi Chapter",
        "preamble_name": "THE SECOND BOOK OF NEPHI",
    },
    {
        "name": "Jacob",
        "prefix": "Jacob",
        "chapters": 7,
        "header": r"THE BOOK OF JACOB",
        "chapter_pattern": "Jacob Chapter",
        "preamble_name": "THE BOOK OF JACOB THE BROTHER OF NEPHI",
    },
    {
        "name": "Enos",
        "prefix": "Enos",
        "chapters": 1,
        "header": r"THE BOOK OF ENOS",
        "chapter_pattern": "Enos Chapter",
        "preamble_name": "THE BOOK OF ENOS",
    },
    {
        "name": "Jarom",
        "prefix": "Jarom",
        "chapters": 1,
        "header": r"THE BOOK OF JAROM",
        "chapter_pattern": "Jarom Chapter",
        "preamble_name": "THE BOOK OF JAROM",
    },
    {
        "name": "Omni",
        "prefix": "Omni",
        "chapters": 1,
        "header": r"THE BOOK OF OMNI",
        "chapter_pattern": "Omni Chapter",
        "preamble_name": "THE BOOK OF OMNI",
    },
    {
        "name": "Words of Mormon",
        "prefix": "WordsOfMormon",
        "chapters": 1,
        "header": r"THE WORDS OF MORMON",
        "chapter_pattern": "Words of Mormon Chapter",
        "preamble_name": "THE WORDS OF MORMON",
    },
    {
        "name": "Mosiah",
        "prefix": "Mosiah",
        "chapters": 29,
        "header": r"THE BOOK OF MOSIAH",
        "chapter_pattern": "Mosiah Chapter",
        "preamble_name": "THE BOOK OF MOSIAH",
    },
    {
        "name": "Alma",
        "prefix": "Alma",
        "chapters": 63,
        "header": r"THE BOOK OF ALMA",
        "chapter_pattern": "Alma Chapter",
        "preamble_name": "THE BOOK OF ALMA THE SON OF ALMA",
    },
    {
        "name": "Helaman",
        "prefix": "Helaman",
        "chapters": 16,
        "header": r"THE BOOK OF HELAMAN",
        "chapter_pattern": "Helaman Chapter",
        "preamble_name": "THE BOOK OF HELAMAN",
    },
    {
        "name": "3 Nephi",
        "prefix": "3Nephi",
        "chapters": 30,
        "header": r"THIRD BOOK OF NEPHI",
        "chapter_pattern": "3 Nephi Chapter",
        "preamble_name": "THIRD NEPHI THE BOOK OF NEPHI",
    },
    {
        "name": "4 Nephi",
        "prefix": "4Nephi",
        "chapters": 1,
        "header": r"FOURTH NEPHI",
        "chapter_pattern": "4 Nephi Chapter",
        "preamble_name": "FOURTH NEPHI THE BOOK OF NEPHI",
    },
    {
        "name": "Mormon",
        "prefix": "Mormon",
        "chapters": 9,
        "header": r"THE BOOK OF MORMON",
        "chapter_pattern": "Mormon Chapter",
        "preamble_name": "THE BOOK OF MORMON",
    },
    {
        "name": "Ether",
        "prefix": "Ether",
        "chapters": 15,
        "header": r"THE BOOK OF ETHER",
        "chapter_pattern": "Ether Chapter",
        "preamble_name": "THE BOOK OF ETHER",
    },
    {
        "name": "Moroni",
        "prefix": "Moroni",
        "chapters": 10,
        "header": r"THE BOOK OF MORONI",
        "chapter_pattern": "Moroni Chapter",
        "preamble_name": "THE BOOK OF MORONI",
    },
]

# === CHAPTER-TO-DATE MAPPING (from existing BOM files / Welch 2018) ===

CHAPTER_DATES = {}

def build_date_map():
    """Build complete chapter-to-date mapping from existing BOM files."""
    date_map = {
        # Mosiah (starts with Mosiah - lost 116 pages mean translation begins here)
        ("Mosiah", 1): "1829-03-31",
        ("Mosiah", 2): "1829-04-07", ("Mosiah", 3): "1829-04-07", ("Mosiah", 4): "1829-04-07",
        ("Mosiah", 5): "1829-04-08", ("Mosiah", 6): "1829-04-08", ("Mosiah", 7): "1829-04-08",
        ("Mosiah", 8): "1829-04-09", ("Mosiah", 9): "1829-04-09", ("Mosiah", 10): "1829-04-09", ("Mosiah", 11): "1829-04-09",
        ("Mosiah", 12): "1829-04-10", ("Mosiah", 13): "1829-04-10", ("Mosiah", 14): "1829-04-10", ("Mosiah", 15): "1829-04-10", ("Mosiah", 16): "1829-04-10",
        ("Mosiah", 17): "1829-04-11", ("Mosiah", 18): "1829-04-11", ("Mosiah", 19): "1829-04-11", ("Mosiah", 20): "1829-04-11",
        ("Mosiah", 21): "1829-04-12", ("Mosiah", 22): "1829-04-12", ("Mosiah", 23): "1829-04-12", ("Mosiah", 24): "1829-04-12", ("Mosiah", 25): "1829-04-12",
        ("Mosiah", 26): "1829-04-13", ("Mosiah", 27): "1829-04-13", ("Mosiah", 28): "1829-04-13",
        ("Mosiah", 29): "1829-04-14",
        # Alma
        ("Alma", 1): "1829-04-14", ("Alma", 2): "1829-04-14",
        ("Alma", 3): "1829-04-15", ("Alma", 4): "1829-04-15", ("Alma", 5): "1829-04-15", ("Alma", 6): "1829-04-15",
        ("Alma", 7): "1829-04-16", ("Alma", 8): "1829-04-16", ("Alma", 9): "1829-04-16", ("Alma", 10): "1829-04-16",
        ("Alma", 11): "1829-04-17", ("Alma", 12): "1829-04-17", ("Alma", 13): "1829-04-17",
        ("Alma", 14): "1829-04-18", ("Alma", 15): "1829-04-18", ("Alma", 16): "1829-04-18", ("Alma", 17): "1829-04-18",
        ("Alma", 18): "1829-04-19", ("Alma", 19): "1829-04-19",
        ("Alma", 20): "1829-04-20", ("Alma", 21): "1829-04-20", ("Alma", 22): "1829-04-20", ("Alma", 23): "1829-04-20",
        ("Alma", 24): "1829-04-21", ("Alma", 25): "1829-04-21", ("Alma", 26): "1829-04-21",
        ("Alma", 27): "1829-04-22", ("Alma", 28): "1829-04-22", ("Alma", 29): "1829-04-22", ("Alma", 30): "1829-04-22",
        ("Alma", 31): "1829-04-23", ("Alma", 32): "1829-04-23", ("Alma", 33): "1829-04-23",
        ("Alma", 34): "1829-04-24", ("Alma", 35): "1829-04-24", ("Alma", 36): "1829-04-24",
        ("Alma", 37): "1829-04-25", ("Alma", 38): "1829-04-25",
        ("Alma", 39): "1829-04-26", ("Alma", 40): "1829-04-26",
        ("Alma", 41): "1829-04-27", ("Alma", 42): "1829-04-27", ("Alma", 43): "1829-04-27",
        ("Alma", 44): "1829-04-28", ("Alma", 45): "1829-04-28",
        ("Alma", 46): "1829-04-29", ("Alma", 47): "1829-04-29", ("Alma", 48): "1829-04-29",
        ("Alma", 49): "1829-04-30", ("Alma", 50): "1829-04-30", ("Alma", 51): "1829-04-30",
        ("Alma", 52): "1829-05-01", ("Alma", 53): "1829-05-01", ("Alma", 54): "1829-05-01",
        ("Alma", 55): "1829-05-02", ("Alma", 56): "1829-05-02", ("Alma", 57): "1829-05-02",
        ("Alma", 58): "1829-05-03", ("Alma", 59): "1829-05-03", ("Alma", 60): "1829-05-03", ("Alma", 61): "1829-05-03",
        ("Alma", 62): "1829-05-04", ("Alma", 63): "1829-05-04",
        # Helaman
        ("Helaman", 1): "1829-05-04",
        ("Helaman", 2): "1829-05-05", ("Helaman", 3): "1829-05-05", ("Helaman", 4): "1829-05-05",
        ("Helaman", 5): "1829-05-06", ("Helaman", 6): "1829-05-06", ("Helaman", 7): "1829-05-06",
        ("Helaman", 8): "1829-05-07", ("Helaman", 9): "1829-05-07", ("Helaman", 10): "1829-05-07",
        ("Helaman", 11): "1829-05-08", ("Helaman", 12): "1829-05-08", ("Helaman", 13): "1829-05-08",
        ("Helaman", 14): "1829-05-09", ("Helaman", 15): "1829-05-09", ("Helaman", 16): "1829-05-09",
        # 3 Nephi
        ("3 Nephi", 1): "1829-05-10", ("3 Nephi", 2): "1829-05-10", ("3 Nephi", 3): "1829-05-10",
        ("3 Nephi", 4): "1829-05-11", ("3 Nephi", 5): "1829-05-11", ("3 Nephi", 6): "1829-05-11",
        ("3 Nephi", 7): "1829-05-12", ("3 Nephi", 8): "1829-05-12", ("3 Nephi", 9): "1829-05-12", ("3 Nephi", 10): "1829-05-12",
        ("3 Nephi", 11): "1829-05-13", ("3 Nephi", 12): "1829-05-13",
        ("3 Nephi", 13): "1829-05-14", ("3 Nephi", 14): "1829-05-14", ("3 Nephi", 15): "1829-05-14",
        ("3 Nephi", 16): "1829-05-15", ("3 Nephi", 17): "1829-05-15", ("3 Nephi", 18): "1829-05-15",
        ("3 Nephi", 19): "1829-05-16", ("3 Nephi", 20): "1829-05-16", ("3 Nephi", 21): "1829-05-16",
        ("3 Nephi", 22): "1829-05-17", ("3 Nephi", 23): "1829-05-17",
        ("3 Nephi", 24): "1829-05-20", ("3 Nephi", 25): "1829-05-20", ("3 Nephi", 26): "1829-05-20", ("3 Nephi", 27): "1829-05-20",
        ("3 Nephi", 28): "1829-05-21", ("3 Nephi", 29): "1829-05-21", ("3 Nephi", 30): "1829-05-21",
        # 4 Nephi
        ("4 Nephi", 1): "1829-05-21",
        # Mormon
        ("Mormon", 1): "1829-05-22", ("Mormon", 2): "1829-05-22", ("Mormon", 3): "1829-05-22", ("Mormon", 4): "1829-05-22",
        ("Mormon", 5): "1829-05-23", ("Mormon", 6): "1829-05-23", ("Mormon", 7): "1829-05-23",
        ("Mormon", 8): "1829-05-24", ("Mormon", 9): "1829-05-24",
        # Ether
        ("Ether", 1): "1829-05-25", ("Ether", 2): "1829-05-25", ("Ether", 3): "1829-05-25",
        ("Ether", 4): "1829-05-26", ("Ether", 5): "1829-05-26", ("Ether", 6): "1829-05-26", ("Ether", 7): "1829-05-26",
        ("Ether", 8): "1829-05-27", ("Ether", 9): "1829-05-27", ("Ether", 10): "1829-05-27",
        ("Ether", 11): "1829-05-28", ("Ether", 12): "1829-05-28",
        ("Ether", 13): "1829-05-29", ("Ether", 14): "1829-05-29", ("Ether", 15): "1829-05-29",
        # Moroni
        ("Moroni", 1): "1829-05-29", ("Moroni", 2): "1829-05-29", ("Moroni", 3): "1829-05-29", ("Moroni", 4): "1829-05-29",
        ("Moroni", 5): "1829-05-30", ("Moroni", 6): "1829-05-30", ("Moroni", 7): "1829-05-30", ("Moroni", 8): "1829-05-30",
        ("Moroni", 9): "1829-05-31", ("Moroni", 10): "1829-05-31",
        # 1 Nephi (translated AFTER Moroni, per Welch)
        ("1 Nephi", 1): "1829-06-05", ("1 Nephi", 2): "1829-06-05",
        ("1 Nephi", 3): "1829-06-06", ("1 Nephi", 4): "1829-06-06", ("1 Nephi", 5): "1829-06-06", ("1 Nephi", 6): "1829-06-06",
        ("1 Nephi", 7): "1829-06-07", ("1 Nephi", 8): "1829-06-07", ("1 Nephi", 9): "1829-06-07",
        ("1 Nephi", 10): "1829-06-08", ("1 Nephi", 11): "1829-06-08", ("1 Nephi", 12): "1829-06-08",
        ("1 Nephi", 13): "1829-06-09", ("1 Nephi", 14): "1829-06-09", ("1 Nephi", 15): "1829-06-09",
        ("1 Nephi", 16): "1829-06-10", ("1 Nephi", 17): "1829-06-10", ("1 Nephi", 18): "1829-06-10", ("1 Nephi", 19): "1829-06-10",
        ("1 Nephi", 20): "1829-06-12", ("1 Nephi", 21): "1829-06-12", ("1 Nephi", 22): "1829-06-12",
        # 2 Nephi
        ("2 Nephi", 1): "1829-06-13", ("2 Nephi", 2): "1829-06-13", ("2 Nephi", 3): "1829-06-13",
        ("2 Nephi", 4): "1829-06-15", ("2 Nephi", 5): "1829-06-15", ("2 Nephi", 6): "1829-06-15",
        ("2 Nephi", 7): "1829-06-16", ("2 Nephi", 8): "1829-06-16", ("2 Nephi", 9): "1829-06-16",
        ("2 Nephi", 10): "1829-06-17", ("2 Nephi", 11): "1829-06-17", ("2 Nephi", 12): "1829-06-17", ("2 Nephi", 13): "1829-06-17",
        ("2 Nephi", 14): "1829-06-18", ("2 Nephi", 15): "1829-06-18", ("2 Nephi", 16): "1829-06-18", ("2 Nephi", 17): "1829-06-18", ("2 Nephi", 18): "1829-06-18", ("2 Nephi", 19): "1829-06-18",
        ("2 Nephi", 20): "1829-06-19", ("2 Nephi", 21): "1829-06-19", ("2 Nephi", 22): "1829-06-19", ("2 Nephi", 23): "1829-06-19", ("2 Nephi", 24): "1829-06-19",
        ("2 Nephi", 25): "1829-06-20", ("2 Nephi", 26): "1829-06-20", ("2 Nephi", 27): "1829-06-20",
        ("2 Nephi", 28): "1829-06-22", ("2 Nephi", 29): "1829-06-22", ("2 Nephi", 30): "1829-06-22", ("2 Nephi", 31): "1829-06-22",
        ("2 Nephi", 32): "1829-06-23", ("2 Nephi", 33): "1829-06-23",
        # Jacob
        ("Jacob", 1): "1829-06-24", ("Jacob", 2): "1829-06-24", ("Jacob", 3): "1829-06-24",
        ("Jacob", 4): "1829-06-25", ("Jacob", 5): "1829-06-25",
        ("Jacob", 6): "1829-06-26", ("Jacob", 7): "1829-06-26",
        # Enos, Jarom, Omni, Words of Mormon
        ("Enos", 1): "1829-06-27",
        ("Jarom", 1): "1829-06-27",
        ("Omni", 1): "1829-06-28",
        ("Words of Mormon", 1): "1829-06-28",
    }
    return date_map


def read_gutenberg_text(filepath):
    """Read the Gutenberg plain text file, stripping the markdown header."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    if '---' in content:
        parts = content.split('---', 1)
        if len(parts) > 1:
            content = parts[1]
    return content.replace('\r', '')


def extract_book_chapters(text, book):
    """Extract all chapters for a given book from the Gutenberg text."""
    chapters = {}
    name = book["name"]
    ch_pattern = book["chapter_pattern"]
    num_ch = book["chapters"]

    # Find the book's preamble
    preamble = ""

    for ch in range(1, num_ch + 1):
        pattern_start = re.escape(ch_pattern) + r' ' + str(ch) + r'\s*\n'

        if ch < num_ch:
            pattern_end = re.escape(ch_pattern) + r' ' + str(ch + 1) + r'\s*\n'
            match = re.search(pattern_start + r'(.*?)' + pattern_end, text, re.DOTALL)
        else:
            # Last chapter — find until next book or end of text
            # Build a list of possible next-book markers
            next_markers = [
                r'THE SECOND BOOK OF NEPHI', r'THE BOOK OF JACOB',
                r'THE BOOK OF ENOS', r'THE BOOK OF JAROM',
                r'THE BOOK OF OMNI', r'THE WORDS OF MORMON',
                r'THE BOOK OF MOSIAH', r'THE BOOK OF ALMA',
                r'THE BOOK OF HELAMAN', r'THIRD BOOK OF NEPHI',
                r'THIRD NEPHI', r'FOURTH NEPHI',
                r'THE BOOK OF MORMON\s*\n\s*\n.*?Mormon Chapter',
                r'THE BOOK OF ETHER', r'THE BOOK OF MORONI',
                r'\*\*\* END OF THE PROJECT GUTENBERG',
            ]
            # Try each marker
            found = False
            for marker in next_markers:
                full_pattern = pattern_start + r'(.*?)(?=' + marker + r')'
                match = re.search(full_pattern, text, re.DOTALL)
                if match:
                    # Make sure we're not matching text within our own book
                    candidate = match.group(1)
                    # Verify this is actually the right end point
                    if len(candidate) > 50:  # reasonable chapter
                        found = True
                        break

            if not found:
                # Fallback: grab a large chunk after the chapter header
                match = re.search(pattern_start + r'(.{100,50000})', text, re.DOTALL)

        if match:
            chapter_text = match.group(1).strip()
            chapters[ch] = chapter_text
        else:
            print(f"  WARNING: Could not extract {name} Chapter {ch}")

    return chapters


def build_diff_header(book_name, chapter, original_date):
    """Build the D&C-style diff header."""
    separator = "═" * 60
    header = f"{separator}\n"
    header += f"TEXTUAL CHANGES — {book_name} {chapter}, Book of Mormon, 1830 (1830-03-26)\n"
    header += f"{separator}\n\n"
    header += f"▶ Changes from Original ({original_date}) → Book of Mormon, 1830 (1830-03-26):\n\n"
    header += "  No meaning-altering changes detected.\n"
    header += f"\n  NOTE: Both the Original and 1830 files currently use the Project\n"
    header += f"  Gutenberg 1830 text as their base. Differences will surface once\n"
    header += f"  the Original files are updated with Printer's Manuscript text\n"
    header += f"  and Skousen's OM corrections from the ATV.\n"
    header += f"\n{separator}\n"
    header += "[Full 1830 edition text follows below]\n"
    header += f"{separator}\n\n"
    return header


def write_chapter_file(filepath, date_str, book_preamble_name, chapter, text, preamble=None):
    """Write a single chapter file."""
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"[{date_str}]\n\n")
        if preamble and chapter == 1:
            f.write(f"{book_preamble_name}\n\n")
        f.write(text)
        f.write("\n")


def main():
    print("=" * 70)
    print("Book of Mormon FULL Extraction — All Books, All Chapters")
    print("=" * 70)

    # Read source text
    print("\n[1] Reading Gutenberg 1830 text...")
    text = read_gutenberg_text(GUTENBERG_FILE)
    print(f"    Read {len(text):,} characters")

    # Build date mapping
    date_map = build_date_map()
    print(f"    Loaded {len(date_map)} chapter-to-date mappings")

    total_1830 = 0
    total_original = 0
    skipped_1nephi = 0

    for book in BOOKS:
        name = book["name"]
        prefix = book["prefix"]
        num_ch = book["chapters"]
        preamble_name = book["preamble_name"]

        print(f"\n{'─' * 50}")
        print(f"  Processing: {name} ({num_ch} chapters)")
        print(f"{'─' * 50}")

        # Skip 1 Nephi (already done in pilot)
        if prefix == "1Nephi":
            print(f"    ⏭  Skipping (already created in pilot batch)")
            skipped_1nephi = 22 * 2  # 22 chapters × 2 editions
            continue

        # Extract chapters
        chapters = extract_book_chapters(text, book)
        print(f"    Extracted {len(chapters)}/{num_ch} chapters")

        for ch, ch_text in sorted(chapters.items()):
            date_key = (name, ch)
            if date_key not in date_map:
                print(f"    ✗ {name} {ch}: No date mapping found!")
                continue

            original_date = date_map[date_key]
            verse_count = len(re.findall(r'\d+:\d+', ch_text))

            # Write 1830 Edition file (with diff header)
            filename_1830 = f"1830-03-26-{prefix}-{ch}-1830.txt"
            filepath_1830 = os.path.join(OUTPUT_DIR, filename_1830)
            diff_header = build_diff_header(name, ch, original_date)

            with open(filepath_1830, 'w', encoding='utf-8') as f:
                f.write(diff_header)
                f.write(f"[1830-03-26]\n\n")
                if ch == 1:
                    f.write(f"{preamble_name}\n\n")
                f.write(f"{book['chapter_pattern']} {ch}\n\n")
                f.write(ch_text)
                f.write("\n")
            total_1830 += 1

            # Write Original Translation file
            filename_orig = f"{original_date}-{prefix}-{ch}-Original.txt"
            filepath_orig = os.path.join(OUTPUT_DIR, filename_orig)

            with open(filepath_orig, 'w', encoding='utf-8') as f:
                f.write(f"[{original_date}]\n\n")
                if ch == 1:
                    f.write(f"{preamble_name}\n\n")
                f.write(f"{book['chapter_pattern']} {ch}\n\n")
                f.write(ch_text)
                f.write("\n")
            total_original += 1

        # Report
        for ch in sorted(chapters.keys()):
            date_key = (name, ch)
            if date_key in date_map:
                v = len(re.findall(r'\d+:\d+', chapters[ch]))
                print(f"    ✓ Ch {ch:2d}: {len(chapters[ch]):6,} chars, ~{v:2d} verses → {date_map[date_key]}")

    # Final summary
    print("\n" + "=" * 70)
    print("EXTRACTION COMPLETE")
    print("=" * 70)
    print(f"  New 1830 Edition files:     {total_1830}")
    print(f"  New Original files:         {total_original}")
    print(f"  Existing (1 Nephi pilot):   {skipped_1nephi}")
    print(f"  TOTAL files:                {total_1830 + total_original + skipped_1nephi}")
    print(f"  Output directory:           {OUTPUT_DIR}")
    print("=" * 70)


if __name__ == "__main__":
    main()
