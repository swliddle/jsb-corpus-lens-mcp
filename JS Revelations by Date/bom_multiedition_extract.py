#!/usr/bin/env python3
"""
Book of Mormon Multi-Edition Extraction from BomDB
====================================================
Uses the BomDB contents.json (Wordtree Foundation) to generate:
  - 1837 Kirtland Edition files with diff headers vs 1830
  - 1840 Nauvoo Edition files with diff headers vs 1837
  
Also regenerates 1830 diff headers using actual 1829 PM text from BomDB.

BomDB editions available: 1829 (PM), 1830, 1837, 1840, 1992
We need: 1837 and 1840 (plus updating Original and 1830 headers)

NOTE: The 1841 Liverpool edition is essentially a reprint of the 1837
Kirtland edition (minor differences only) — will be handled separately.
"""

import json
import os
import re

# === CONFIGURATION ===

BOMDB_FILE = "/Users/ericdenna/Library/CloudStorage/GoogleDrive-eric.denna@gmail.com/My Drive/! AAA Personal - WIP/! Joseph the Prophet/JSB - WIP/JSB Doctrinal Learning  over time/JS Revelations by Date/bomdb_contents.json"

OUTPUT_DIR = "/Users/ericdenna/Library/CloudStorage/GoogleDrive-eric.denna@gmail.com/My Drive/! AAA Personal - WIP/! Joseph the Prophet/JSB - WIP/JSB Doctrinal Learning  over time/JS Revelations by Date"

# Book name mapping: BomDB name → our file prefix
BOOK_MAP = {
    "1 Nephi": "1Nephi",
    "2 Nephi": "2Nephi",
    "Jacob": "Jacob",
    "Enos": "Enos",
    "Jarom": "Jarom",
    "Omni": "Omni",
    "Words of Mormon": "WordsOfMormon",
    "Mosiah": "Mosiah",
    "Alma": "Alma",
    "Helaman": "Helaman",
    "3 Nephi": "3Nephi",
    "4 Nephi": "4Nephi",
    "Mormon": "Mormon",
    "Ether": "Ether",
    "Moroni": "Moroni",
}

# Edition dates (when the edition was published/became available)
EDITION_DATES = {
    "1837": "1837-02-01",  # 1837 Kirtland
    "1840": "1840-10-03",  # 1840 Nauvoo
}

# Edition labels for headers
EDITION_LABELS = {
    "1837": "1837 Kirtland",
    "1840": "1840 Nauvoo",
}

# What each edition should be diffed against
EDITION_PREDECESSOR = {
    "1837": "1830",
    "1840": "1837",
}

# Chapter-to-translation-date mapping (for Original)
CHAPTER_DATES = {
    ("Mosiah", 1): "1829-03-31",
    ("Mosiah", 2): "1829-04-07", ("Mosiah", 3): "1829-04-07", ("Mosiah", 4): "1829-04-07",
    ("Mosiah", 5): "1829-04-08", ("Mosiah", 6): "1829-04-08", ("Mosiah", 7): "1829-04-08",
    ("Mosiah", 8): "1829-04-09", ("Mosiah", 9): "1829-04-09", ("Mosiah", 10): "1829-04-09", ("Mosiah", 11): "1829-04-09",
    ("Mosiah", 12): "1829-04-10", ("Mosiah", 13): "1829-04-10", ("Mosiah", 14): "1829-04-10", ("Mosiah", 15): "1829-04-10", ("Mosiah", 16): "1829-04-10",
    ("Mosiah", 17): "1829-04-11", ("Mosiah", 18): "1829-04-11", ("Mosiah", 19): "1829-04-11", ("Mosiah", 20): "1829-04-11",
    ("Mosiah", 21): "1829-04-12", ("Mosiah", 22): "1829-04-12", ("Mosiah", 23): "1829-04-12", ("Mosiah", 24): "1829-04-12", ("Mosiah", 25): "1829-04-12",
    ("Mosiah", 26): "1829-04-13", ("Mosiah", 27): "1829-04-13", ("Mosiah", 28): "1829-04-13",
    ("Mosiah", 29): "1829-04-14",
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
    ("Helaman", 1): "1829-05-04",
    ("Helaman", 2): "1829-05-05", ("Helaman", 3): "1829-05-05", ("Helaman", 4): "1829-05-05",
    ("Helaman", 5): "1829-05-06", ("Helaman", 6): "1829-05-06", ("Helaman", 7): "1829-05-06",
    ("Helaman", 8): "1829-05-07", ("Helaman", 9): "1829-05-07", ("Helaman", 10): "1829-05-07",
    ("Helaman", 11): "1829-05-08", ("Helaman", 12): "1829-05-08", ("Helaman", 13): "1829-05-08",
    ("Helaman", 14): "1829-05-09", ("Helaman", 15): "1829-05-09", ("Helaman", 16): "1829-05-09",
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
    ("4 Nephi", 1): "1829-05-21",
    ("Mormon", 1): "1829-05-22", ("Mormon", 2): "1829-05-22", ("Mormon", 3): "1829-05-22", ("Mormon", 4): "1829-05-22",
    ("Mormon", 5): "1829-05-23", ("Mormon", 6): "1829-05-23", ("Mormon", 7): "1829-05-23",
    ("Mormon", 8): "1829-05-24", ("Mormon", 9): "1829-05-24",
    ("Ether", 1): "1829-05-25", ("Ether", 2): "1829-05-25", ("Ether", 3): "1829-05-25",
    ("Ether", 4): "1829-05-26", ("Ether", 5): "1829-05-26", ("Ether", 6): "1829-05-26", ("Ether", 7): "1829-05-26",
    ("Ether", 8): "1829-05-27", ("Ether", 9): "1829-05-27", ("Ether", 10): "1829-05-27",
    ("Ether", 11): "1829-05-28", ("Ether", 12): "1829-05-28",
    ("Ether", 13): "1829-05-29", ("Ether", 14): "1829-05-29", ("Ether", 15): "1829-05-29",
    ("Moroni", 1): "1829-05-29", ("Moroni", 2): "1829-05-29", ("Moroni", 3): "1829-05-29", ("Moroni", 4): "1829-05-29",
    ("Moroni", 5): "1829-05-30", ("Moroni", 6): "1829-05-30", ("Moroni", 7): "1829-05-30", ("Moroni", 8): "1829-05-30",
    ("Moroni", 9): "1829-05-31", ("Moroni", 10): "1829-05-31",
    ("1 Nephi", 1): "1829-06-05", ("1 Nephi", 2): "1829-06-05",
    ("1 Nephi", 3): "1829-06-06", ("1 Nephi", 4): "1829-06-06", ("1 Nephi", 5): "1829-06-06", ("1 Nephi", 6): "1829-06-06",
    ("1 Nephi", 7): "1829-06-07", ("1 Nephi", 8): "1829-06-07", ("1 Nephi", 9): "1829-06-07",
    ("1 Nephi", 10): "1829-06-08", ("1 Nephi", 11): "1829-06-08", ("1 Nephi", 12): "1829-06-08",
    ("1 Nephi", 13): "1829-06-09", ("1 Nephi", 14): "1829-06-09", ("1 Nephi", 15): "1829-06-09",
    ("1 Nephi", 16): "1829-06-10", ("1 Nephi", 17): "1829-06-10", ("1 Nephi", 18): "1829-06-10", ("1 Nephi", 19): "1829-06-10",
    ("1 Nephi", 20): "1829-06-12", ("1 Nephi", 21): "1829-06-12", ("1 Nephi", 22): "1829-06-12",
    ("2 Nephi", 1): "1829-06-13", ("2 Nephi", 2): "1829-06-13", ("2 Nephi", 3): "1829-06-13",
    ("2 Nephi", 4): "1829-06-15", ("2 Nephi", 5): "1829-06-15", ("2 Nephi", 6): "1829-06-15",
    ("2 Nephi", 7): "1829-06-16", ("2 Nephi", 8): "1829-06-16", ("2 Nephi", 9): "1829-06-16",
    ("2 Nephi", 10): "1829-06-17", ("2 Nephi", 11): "1829-06-17", ("2 Nephi", 12): "1829-06-17", ("2 Nephi", 13): "1829-06-17",
    ("2 Nephi", 14): "1829-06-18", ("2 Nephi", 15): "1829-06-18", ("2 Nephi", 16): "1829-06-18", ("2 Nephi", 17): "1829-06-18", ("2 Nephi", 18): "1829-06-18", ("2 Nephi", 19): "1829-06-18",
    ("2 Nephi", 20): "1829-06-19", ("2 Nephi", 21): "1829-06-19", ("2 Nephi", 22): "1829-06-19", ("2 Nephi", 23): "1829-06-19", ("2 Nephi", 24): "1829-06-19",
    ("2 Nephi", 25): "1829-06-20", ("2 Nephi", 26): "1829-06-20", ("2 Nephi", 27): "1829-06-20",
    ("2 Nephi", 28): "1829-06-22", ("2 Nephi", 29): "1829-06-22", ("2 Nephi", 30): "1829-06-22", ("2 Nephi", 31): "1829-06-22",
    ("2 Nephi", 32): "1829-06-23", ("2 Nephi", 33): "1829-06-23",
    ("Jacob", 1): "1829-06-24", ("Jacob", 2): "1829-06-24", ("Jacob", 3): "1829-06-24",
    ("Jacob", 4): "1829-06-25", ("Jacob", 5): "1829-06-25",
    ("Jacob", 6): "1829-06-26", ("Jacob", 7): "1829-06-26",
    ("Enos", 1): "1829-06-27",
    ("Jarom", 1): "1829-06-27",
    ("Omni", 1): "1829-06-28",
    ("Words of Mormon", 1): "1829-06-28",
}


def find_meaning_changes(earlier_verses, later_verses, verse_refs):
    """Compare two sets of verse texts and identify meaning-altering changes."""
    changes = []
    change_num = 0
    
    for ref in verse_refs:
        earlier = earlier_verses.get(ref, "")
        later = later_verses.get(ref, "")
        
        if earlier == later:
            continue
        
        # Normalize for comparison: lowercase, remove extra spaces, standardize punctuation
        e_norm = re.sub(r'[;:,.\-\!\?]', '', earlier.lower()).split()
        l_norm = re.sub(r'[;:,.\-\!\?]', '', later.lower()).split()
        
        if e_norm == l_norm:
            continue  # Only punctuation/capitalization changes
        
        # Find the specific word differences
        # Use set difference for a rough check first
        e_set = set(e_norm)
        l_set = set(l_norm)
        added_words = l_set - e_set
        removed_words = e_set - l_set
        
        if not added_words and not removed_words:
            continue  # Just reordering or trivial
        
        change_num += 1
        verse_num = ref.split(":")[-1] if ":" in ref else ref
        
        # Determine change type
        if len(earlier) < len(later) * 0.7:
            change_type = "PHRASE ADDITION"
        elif len(later) < len(earlier) * 0.7:
            change_type = "PHRASE REMOVAL"
        else:
            change_type = "WORD CHANGE"
        
        # Truncate long lines for header readability
        e_display = earlier[:150] + "..." if len(earlier) > 150 else earlier
        l_display = later[:150] + "..." if len(later) > 150 else later
        
        change_desc = f"  {change_num}. {change_type} ({ref}):\n"
        change_desc += f'     EARLIER: "{e_display}"\n'
        change_desc += f'     LATER:   "{l_display}"\n'
        
        changes.append(change_desc)
    
    return changes


def build_diff_header(book_name, chapter, edition, edition_date, predecessor, pred_date, changes):
    """Build the D&C-style diff header."""
    sep = "\u2550" * 60
    header = f"{sep}\n"
    header += f"TEXTUAL CHANGES \u2014 {book_name} {chapter}, Book of Mormon, {EDITION_LABELS.get(edition, edition)} ({edition_date})\n"
    header += f"{sep}\n\n"
    header += f"\u25b6 Changes from {EDITION_LABELS.get(predecessor, predecessor)} ({pred_date}) \u2192 {EDITION_LABELS.get(edition, edition)} ({edition_date}):\n\n"
    
    if not changes:
        header += "  No meaning-altering changes detected.\n"
    else:
        for change in changes:
            header += change + "\n"
    
    header += f"\n{sep}\n"
    header += f"[Full {EDITION_LABELS.get(edition, edition)} edition text follows below]\n"
    header += f"{sep}\n\n"
    
    return header


def main():
    print("=" * 70)
    print("Book of Mormon Multi-Edition Extraction from BomDB")
    print("=" * 70)
    
    # Load BomDB data
    print("\n[1] Loading BomDB contents.json...")
    with open(BOMDB_FILE, 'r') as f:
        data = json.load(f)
    
    contents = data["contents"]
    print(f"    Books: {len(contents)}")
    
    # Process each edition we need
    for edition in ["1837", "1840"]:
        predecessor = EDITION_PREDECESSOR[edition]
        edition_date = EDITION_DATES[edition]
        edition_label = EDITION_LABELS[edition]
        
        print(f"\n{'=' * 70}")
        print(f"  EDITION: {edition_label} ({edition_date})")
        print(f"  Comparing against: {EDITION_LABELS.get(predecessor, predecessor)}")
        print(f"{'=' * 70}")
        
        total_files = 0
        total_changes = 0
        
        for book_name, chapters in contents.items():
            prefix = BOOK_MAP.get(book_name)
            if not prefix:
                print(f"  WARNING: Unknown book '{book_name}', skipping")
                continue
            
            for ch_str, verses in sorted(chapters.items(), key=lambda x: int(x[0])):
                ch = int(ch_str)
                
                # Get original date for predecessor reference
                date_key = (book_name, ch)
                orig_date = CHAPTER_DATES.get(date_key, "unknown")
                
                # Predecessor date
                if predecessor == "1830":
                    pred_date = "1830-03-26"
                elif predecessor == "1837":
                    pred_date = EDITION_DATES["1837"]
                else:
                    pred_date = orig_date
                
                # Collect verse texts for both editions
                verse_refs = sorted(verses.keys(), key=lambda v: [int(x) for x in re.findall(r'\d+', v)])
                
                earlier_verses = {}
                later_verses = {}
                
                for ref, editions_text in verses.items():
                    earlier_verses[ref] = editions_text.get(predecessor, "")
                    later_verses[ref] = editions_text.get(edition, "")
                
                # Find changes
                changes = find_meaning_changes(earlier_verses, later_verses, verse_refs)
                total_changes += len(changes)
                
                # Build the chapter text
                chapter_text_parts = []
                for ref in verse_refs:
                    text = later_verses.get(ref, "")
                    if text:
                        chapter_text_parts.append(f"{ref} {text}")
                
                chapter_text = "\n\n".join(chapter_text_parts)
                
                # Build header
                header = build_diff_header(
                    book_name, ch, edition, edition_date,
                    predecessor, pred_date, changes
                )
                
                # Write file
                filename = f"{edition_date}-{prefix}-{ch}-{edition}.txt"
                filepath = os.path.join(OUTPUT_DIR, filename)
                
                with open(filepath, 'w') as f:
                    f.write(header)
                    f.write(f"[{edition_date}]\n\n")
                    f.write(chapter_text)
                    f.write("\n")
                
                total_files += 1
            
        print(f"\n  Files created: {total_files}")
        print(f"  Total changes found: {total_changes}")
    
    # Final grand total
    print(f"\n{'=' * 70}")
    print("MULTI-EDITION EXTRACTION COMPLETE")
    print(f"{'=' * 70}")
    
    # Count all files
    for ed, ed_date in EDITION_DATES.items():
        count = len([f for f in os.listdir(OUTPUT_DIR) if f.endswith(f"-{ed}.txt")])
        print(f"  {EDITION_LABELS[ed]}: {count} files")
    
    count_1830 = len([f for f in os.listdir(OUTPUT_DIR) if f.endswith("-1830.txt")])
    count_orig = len([f for f in os.listdir(OUTPUT_DIR) if f.endswith("-Original.txt")])
    print(f"  1830 Palmyra:     {count_1830} files")
    print(f"  Original:         {count_orig} files")
    total = sum(1 for f in os.listdir(OUTPUT_DIR) if f.endswith(('.txt',)) and any(e in f for e in ['-1830.txt', '-Original.txt', '-1837.txt', '-1840.txt']))
    print(f"  GRAND TOTAL:      {total} files")


if __name__ == "__main__":
    main()
